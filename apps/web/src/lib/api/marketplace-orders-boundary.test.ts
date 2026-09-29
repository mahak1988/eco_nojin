import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  type ApiFailureKind,
  classifyApiFailure,
  getOrder,
  getOrderTimeline,
  listOrders,
  ORDER_STATUSES,
} from './cart';
import { setApiBaseUrl } from './client';
import {
  isRedirectGateway,
  isValidTransactionKey,
  REDIRECT_GATEWAYS,
  transactionKeySchema,
} from './escrow';
import {
  getProductTrace,
  listProducts,
  PRODUCT_FILTER_PARAMS,
  parseProductFilterForm,
  productTraceSource,
  SEARCH_SOURCE,
  searchProducts,
} from './market';

const API_BASE = 'https://api.example.test';

function stubFetch(body: unknown, status = 200) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', fetchMock);
  setApiBaseUrl(API_BASE);
  return fetchMock;
}

function firstUrl(fetchMock: ReturnType<typeof vi.fn>): string {
  const [url] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
  return url;
}

const ORDER = {
  id: 'order-1',
  product_name: 'Barley',
  buyer_name: 'Buyer',
  seller_id: 'seller-1',
  quantity_kg: 2,
  total_price: 300,
  status: 'pending',
  created_at: '2026-09-20T10:00:00',
};

describe('order list and lookup boundary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('reads the order list from the gateway', async () => {
    const fetchMock = stubFetch({ orders: [ORDER], count: 1 });

    const result = await listOrders();

    expect(result.ok).toBe(true);
    expect(firstUrl(fetchMock)).toBe(`${API_BASE}/api/v1/marketplace/orders`);
  });

  it('sends only the statuses the gateway models', async () => {
    const fetchMock = stubFetch({ orders: [], count: 0 });

    await listOrders('shipped');

    expect(firstUrl(fetchMock)).toBe(`${API_BASE}/api/v1/marketplace/orders?status=shipped`);
    expect([...ORDER_STATUSES]).toEqual([
      'pending',
      'confirmed',
      'shipped',
      'delivered',
      'cancelled',
    ]);
  });

  it('refuses an unknown status instead of letting the gateway return everything', async () => {
    const fetchMock = stubFetch({ orders: [ORDER], count: 1 });

    const result = await listOrders('refunded' as (typeof ORDER_STATUSES)[number]);

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('resolves one order and keeps the server amount', async () => {
    stubFetch({ orders: [ORDER], count: 1 });

    const result = await getOrder('order-1');

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.data.total_price).toBe(300);
  });

  it('reports a missing order as not found rather than an empty success', async () => {
    stubFetch({ orders: [], count: 0 });

    const result = await getOrder('order-404');

    expect(result.ok).toBe(false);
    if (result.ok) return;
    const kind: ApiFailureKind = classifyApiFailure(result.status);
    expect(kind).toBe('not-found');
  });

  it('rejects an order payload that does not match the gateway contract', async () => {
    stubFetch({ orders: [{ ...ORDER, total_price: 'three hundred' }], count: 1 });

    const result = await getOrder('order-1');

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.status).toBe(502);
    expect(result.error).toContain('total_price');
  });

  it('reads the order timeline from the tracking endpoint', async () => {
    const fetchMock = stubFetch({
      order_id: 'order-1',
      order_number: 'ECO-1',
      current_status: 'pending',
      timeline: [
        {
          timestamp: '2026-09-20T10:00:00',
          status: 'pending',
          title: 'Order placed',
          description: 'Waiting for seller confirmation',
        },
      ],
    });

    const result = await getOrderTimeline('order-1');

    expect(result.ok).toBe(true);
    expect(firstUrl(fetchMock)).toBe(`${API_BASE}/api/v1/marketplace/orders/order-1/track`);
  });
});

describe('product trace and search boundary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('reads the traceability record and keeps the gateway event fields', async () => {
    const fetchMock = stubFetch({
      product_id: 'p1',
      traceability_code: 'TR-1',
      events: [
        {
          timestamp: '2026-09-01T08:00:00',
          event: 'harvest',
          location: 'Kurdistan',
          actor: 'Farm',
          notes: 'Lot A',
        },
      ],
      qr_data: 'eco://trace/TR-1',
    });

    const result = await getProductTrace('p1');

    expect(result.ok).toBe(true);
    expect(firstUrl(fetchMock)).toBe(`${API_BASE}/api/v1/marketplace/products/p1/trace`);
    expect(productTraceSource('p 1')).toBe('/api/v1/marketplace/products/p%201/trace');
    if (!result.ok) return;
    expect(result.data.events[0].notes).toBe('Lot A');
    expect(result.data.qr_data).toBe('eco://trace/TR-1');
  });

  it('reports a missing product as a not-found failure', async () => {
    stubFetch({ detail: 'Product not found' }, 404);

    const result = await getProductTrace('missing');

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(classifyApiFailure(result.status)).toBe('not-found');
  });

  it('sends the keyword search to the connected search endpoint', async () => {
    const fetchMock = stubFetch({
      query: 'barley',
      results: [{ id: 'p1', name: 'Barley', price_per_kg: 150 }],
      count: 1,
    });

    const result = await searchProducts('barley');

    expect(result.ok).toBe(true);
    expect(SEARCH_SOURCE).toBe('/api/v1/marketplace/products/search');
    expect(firstUrl(fetchMock)).toBe(`${API_BASE}/api/v1/marketplace/products/search?q=barley`);
  });

  it('only emits query parameters the product list endpoint accepts', async () => {
    const fetchMock = stubFetch({ products: [], count: 0 });

    const parsed = parseProductFilterForm({
      category: 'grain',
      organic: true,
      priceMin: '10',
      priceMax: '900',
      limit: '25',
    });

    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.applied).toEqual([...PRODUCT_FILTER_PARAMS]);

    await listProducts(parsed.filters);

    const url = new URL(firstUrl(fetchMock));
    expect([...url.searchParams.keys()].sort()).toEqual([
      'category',
      'limit',
      'max_price',
      'min_price',
      'organic_only',
    ]);
    expect(url.searchParams.get('category')).toBe('grain');
    expect(url.searchParams.get('limit')).toBe('25');
  });

  it('drops a filter the form left blank instead of sending an empty parameter', async () => {
    const fetchMock = stubFetch({ products: [], count: 0 });

    const parsed = parseProductFilterForm({
      category: '  ',
      organic: false,
      priceMin: '',
      priceMax: '',
      limit: '',
    });

    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.applied).toEqual(['limit']);

    await listProducts(parsed.filters);

    const url = new URL(firstUrl(fetchMock));
    expect([...url.searchParams.keys()]).toEqual(['limit']);
    expect(url.searchParams.get('limit')).toBe('50');
  });

  it('rejects a filter form the endpoint could not honour', () => {
    const notANumber = parseProductFilterForm({
      category: '',
      organic: false,
      priceMin: 'cheap',
      priceMax: '',
      limit: '',
    });
    expect(notANumber.ok).toBe(false);
    if (notANumber.ok) return;
    expect(notANumber.issues.join(' ')).toContain('priceMin');

    const negative = parseProductFilterForm({
      category: '',
      organic: false,
      priceMin: '-5',
      priceMax: '',
      limit: '',
    });
    expect(negative.ok).toBe(false);

    const inverted = parseProductFilterForm({
      category: '',
      organic: false,
      priceMin: '900',
      priceMax: '10',
      limit: '',
    });
    expect(inverted.ok).toBe(false);

    const zeroLimit = parseProductFilterForm({
      category: '',
      organic: false,
      priceMin: '',
      priceMax: '',
      limit: '0',
    });
    expect(zeroLimit.ok).toBe(false);
  });
});

describe('payment redirect and reference contracts', () => {
  it('offers only the gateways that answer with a redirect url', () => {
    expect([...REDIRECT_GATEWAYS]).toEqual(['zarinpal', 'international']);
    expect(isRedirectGateway('zarinpal')).toBe(true);
    expect(isRedirectGateway('bank')).toBe(false);
  });

  it('holds the bank tracking code to the gateway contract', () => {
    expect(isValidTransactionKey(' 88213 ')).toBe(true);
    expect(isValidTransactionKey('')).toBe(false);
    expect(isValidTransactionKey('x'.repeat(121))).toBe(false);
    expect(transactionKeySchema.safeParse('x'.repeat(120)).success).toBe(true);
  });
});
