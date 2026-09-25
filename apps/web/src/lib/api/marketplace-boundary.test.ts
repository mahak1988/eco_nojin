import { afterEach, describe, expect, it, vi } from 'vitest';
import { addToCart, classifyApiFailure, createOrder, getCart } from './cart';
import { setApiBaseUrl } from './client';
import {
  confirmPayment,
  createPayment,
  getEscrowStatus,
  heldAmount,
  isPaymentGateway,
  openDispute,
  PAYMENT_GATEWAYS,
  settleOrder,
} from './escrow';
import { listProducts, searchProducts } from './market';

const API_BASE = 'https://api.example.test';

function stubFetch(body: unknown, status = 200) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', fetchMock);
  setApiBaseUrl(API_BASE);
  return fetchMock;
}

function requestHeaders(fetchMock: ReturnType<typeof vi.fn>, index = 0): Headers {
  const [, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return new Headers(init.headers);
}

describe('marketplace cart and order boundary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('reads the cart from the gateway without client-side enrichment', async () => {
    const fetchMock = stubFetch({
      cart_id: 'cart-1',
      items: [{ product_id: 'p1', product_name: 'Barley', quantity: 2, price: 150 }],
      total_items: 2,
      subtotal: 300,
    });

    const result = await getCart();

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.subtotal).toBe(300);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE}/api/v1/marketplace/cart`);
    expect(init.method ?? 'GET').toBe('GET');
    expect(requestHeaders(fetchMock).get('X-CSRF-Intent')).toBeNull();
  });

  it('sends an idempotency key and CSRF intent for cart writes', async () => {
    const fetchMock = stubFetch({ cart_id: 'cart-1', items: [], total_items: 0, subtotal: 0 }, 201);

    await addToCart([{ productId: 'p1', quantity: 2 }]);

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe('POST');
    const headers = requestHeaders(fetchMock);
    expect(headers.get('Idempotency-Key')).toBeTruthy();
    expect(headers.get('X-CSRF-Intent')).toBe('1');
    expect(JSON.parse(String(init.body))).toEqual({ items: [{ product_id: 'p1', quantity: 2 }] });
  });

  it('creates an order from the cart line and reports the server amount', async () => {
    const fetchMock = stubFetch({
      order_id: 'order-1',
      product_name: 'Barley',
      quantity_kg: 2,
      total_price: 300,
      status: 'pending',
      traceability_code: 'TR-1',
    });

    const result = await createOrder({ productId: 'p1', buyerName: 'Buyer', quantityKg: 2 });

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.total_price).toBe(300);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE}/api/v1/marketplace/orders`);
    expect(JSON.parse(String(init.body))).toEqual({
      product_id: 'p1',
      buyer_name: 'Buyer',
      quantity_kg: 2,
    });
    expect(requestHeaders(fetchMock).get('Idempotency-Key')).toBeTruthy();
  });

  it('classifies a rejected session as an auth failure, not a generic error', async () => {
    stubFetch({ detail: 'Not authenticated' }, 401);

    const result = await getCart();

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(classifyApiFailure(result.status)).toBe('auth');
    expect(result.error).toBe('Not authenticated');
  });

  it('classifies a transport failure as offline', () => {
    expect(classifyApiFailure(0)).toBe('offline');
    expect(classifyApiFailure(403)).toBe('auth');
    expect(classifyApiFailure(404)).toBe('not-found');
    expect(classifyApiFailure(500)).toBe('server');
  });
});

describe('marketplace payment and escrow boundary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('only accepts the gateways the gateway implements', () => {
    expect([...PAYMENT_GATEWAYS]).toEqual(['zarinpal', 'bank', 'international']);
    expect(isPaymentGateway('bank')).toBe(true);
    expect(isPaymentGateway('ecowallet')).toBe(false);
    expect(isPaymentGateway('card')).toBe(false);
  });

  it('charges the server order total and marks the payment idempotent', async () => {
    const fetchMock = stubFetch(
      {
        id: 'pay-1',
        order_id: 'order-1',
        gateway: 'bank',
        amount: 300,
        currency: 'IRR',
        status: 'awaiting_verification',
        escrow_status: 'none',
        redirect_url: null,
        ref_id: null,
        created_at: null,
      },
      201,
    );

    const result = await createPayment({
      orderId: 'order-1',
      amount: 300,
      paymentMethod: 'bank',
    });

    expect(result.ok).toBe(true);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE}/api/v1/marketplace/payments`);
    expect(JSON.parse(String(init.body))).toEqual({
      order_id: 'order-1',
      amount: 300,
      payment_method: 'bank',
      description: '',
    });
    const headers = requestHeaders(fetchMock);
    expect(headers.get('Idempotency-Key')).toBeTruthy();
    expect(headers.get('X-CSRF-Intent')).toBe('1');
  });

  it('keeps every financial transition idempotent', async () => {
    const fetchMock = stubFetch({ order_id: 'order-1', escrow_id: 'esc-1', state: 'disputed' });
    setApiBaseUrl(API_BASE);

    await confirmPayment('pay-1', 'ref-9');
    await openDispute('order-1');
    await settleOrder('order-1');

    expect(fetchMock).toHaveBeenCalledTimes(3);
    for (let index = 0; index < 3; index += 1) {
      const [, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
      expect(init.method).toBe('POST');
      const headers = new Headers(init.headers);
      expect(headers.get('Idempotency-Key')).toBeTruthy();
      expect(headers.get('X-CSRF-Intent')).toBe('1');
    }
  });

  it('derives the held amount only from real ledger entries', () => {
    expect(
      heldAmount([
        { id: 'e1', entry_type: 'hold', amount: 300 },
        { id: 'e2', entry_type: 'release', amount: 300 },
      ]),
    ).toBe(300);
    expect(heldAmount([{ id: 'e1', entry_type: 'release', amount: 300 }])).toBeNull();
    expect(heldAmount([])).toBeNull();
  });

  it('surfaces a missing escrow record instead of an empty success', async () => {
    stubFetch({ detail: 'Payment not found' }, 404);

    const result = await getEscrowStatus('missing');

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(classifyApiFailure(result.status)).toBe('not-found');
  });
});

describe('marketplace catalogue mapping', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('leaves fields the list endpoint omits undefined', async () => {
    stubFetch({
      products: [
        {
          id: 'p1',
          name: 'Barley',
          category: 'grain',
          description: '',
          price_per_kg: 150,
          quantity_available_kg: 40,
          organic_certified: true,
          producer_name: 'Farm',
          origin_location: 'Kurdistan',
          traceability_code: 'TR-1',
          images: [],
        },
      ],
      count: 1,
    });

    const result = await listProducts({});

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const [product] = result.data.products;
    expect(product.price).toBe(150);
    expect(product.stockQuantity).toBe(40);
    expect(product.organic).toBe(true);
    // The list endpoint sends no footprint fields: they must stay absent.
    expect(product.carbonFootprint).toBeUndefined();
    expect(product.waterFootprint).toBeUndefined();
  });

  it('returns only the real fields for search hits', async () => {
    stubFetch({
      query: 'barley',
      results: [{ id: 'p1', name: 'Barley', price_per_kg: 150 }],
      count: 1,
    });

    const result = await searchProducts('barley');

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data).toEqual([{ id: 'p1', name: 'Barley', pricePerKg: 150 }]);
  });
});
