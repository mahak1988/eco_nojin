import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setApiBaseUrl } from '@/lib/api/client';

const push = vi.fn();
const searchParams = new URLSearchParams();
const authState: { user: { id: string; full_name: string } | null; loading: boolean } = {
  user: { id: 'user-1', full_name: 'Buyer' },
  loading: false,
};

vi.mock('next/navigation', () => ({
  usePathname: () => '/fa/market/checkout/card',
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}));

vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => authState,
}));

const { default: CardPaymentPage } = await import('./page');

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

const PAYMENT = {
  id: 'pay-1',
  order_id: 'order-1',
  gateway: 'zarinpal',
  amount: 300,
  currency: 'IRR',
  status: 'redirected',
  escrow_status: 'none',
  redirect_url: 'https://gateway.example.test/pay/authority-1',
  ref_id: null,
  created_at: '2026-09-20T10:05:00',
};

function stubFetch(bodies: unknown[], status = 200) {
  let call = 0;
  const fetchMock = vi.fn(async () => {
    const body = bodies[Math.min(call, bodies.length - 1)];
    call += 1;
    return new Response(JSON.stringify(body), { status });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

beforeEach(() => {
  setApiBaseUrl('https://api.example.test');
  searchParams.delete('order');
  searchParams.delete('payment');
  searchParams.set('order', 'order-1');
  authState.user = { id: 'user-1', full_name: 'Buyer' };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setApiBaseUrl('http://127.0.0.1:8000');
  push.mockClear();
});

describe('checkout card page', () => {
  it('collects no card data and only shows the gateway step', async () => {
    stubFetch([{ orders: [ORDER], count: 1 }]);

    const { container } = render(<CardPaymentPage />);

    expect(await screen.findByText('order-1')).not.toBeNull();
    const inputs = container.querySelectorAll('input');
    expect(inputs.length).toBe(0);
    expect(container.querySelector('form')).toBeNull();
  });

  it('charges the server order total and hands over to the gateway redirect', async () => {
    const fetchMock = stubFetch([{ orders: [ORDER], count: 1 }, PAYMENT]);
    const assign = vi.fn();
    vi.stubGlobal('location', { ...window.location, assign });

    render(<CardPaymentPage />);

    const open = await screen.findByText('open');
    fireEvent.click(open.closest('button') as HTMLButtonElement);

    await waitFor(() => expect(assign).toHaveBeenCalledWith(PAYMENT.redirect_url));
    const [, init] = fetchMock.mock.calls[1] as unknown as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      order_id: 'order-1',
      amount: 300,
      payment_method: 'zarinpal',
      description: 'Barley',
    });
    const [url] = fetchMock.mock.calls[1] as unknown as [string];
    expect(url).toBe('https://api.example.test/api/v1/marketplace/payments');
  });

  it('reports a missing order as unavailable instead of inventing a payment', async () => {
    const fetchMock = stubFetch([{ orders: [], count: 0 }]);

    render(<CardPaymentPage />);

    expect(await screen.findByText('unavailable')).not.toBeNull();
    const posts = (fetchMock.mock.calls as unknown as Array<[string, RequestInit]>).filter(
      ([, init]) => init.method === 'POST',
    );
    expect(posts).toHaveLength(0);
  });

  it('asks for a session before touching the payment endpoint', async () => {
    const fetchMock = stubFetch([{ orders: [ORDER], count: 1 }]);
    authState.user = null;

    render(<CardPaymentPage />);

    expect(await screen.findByText('signedOut')).not.toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
