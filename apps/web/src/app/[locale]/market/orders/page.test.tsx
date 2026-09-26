import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setApiBaseUrl } from '@/lib/api/client';

const push = vi.fn();
const authState: { user: { id: string; full_name: string } | null; loading: boolean } = {
  user: { id: 'user-1', full_name: 'Buyer' },
  loading: false,
};

vi.mock('next/navigation', () => ({
  usePathname: () => '/fa/market/orders',
  useRouter: () => ({ push }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}));

vi.mock('@/components/providers/AuthProvider', () => ({
  useAuth: () => authState,
}));

const { default: OrdersPage } = await import('./page');

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

function stubFetch(body: unknown, status = 200) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

beforeEach(() => {
  setApiBaseUrl('https://api.example.test');
  authState.user = { id: 'user-1', full_name: 'Buyer' };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setApiBaseUrl('http://127.0.0.1:8000');
  push.mockClear();
});

describe('market orders page', () => {
  it('renders the order fields the gateway returned', async () => {
    const fetchMock = stubFetch({ orders: [ORDER], count: 1 });

    render(<OrdersPage />);

    expect(await screen.findByText('Barley')).not.toBeNull();
    expect(screen.getByText(/order-1/)).not.toBeNull();
    expect(screen.getByText('Buyer')).not.toBeNull();
    expect(screen.getByText('seller-1')).not.toBeNull();
    // The status appears on the order row and as a filter option.
    expect(screen.getAllByText('pending').length).toBeGreaterThan(0);
    const [url] = fetchMock.mock.calls[0] as unknown as [string];
    expect(url).toBe('https://api.example.test/api/v1/marketplace/orders');
  });

  it('shows the empty state when the gateway returned no order', async () => {
    stubFetch({ orders: [], count: 0 });

    render(<OrdersPage />);

    expect(await screen.findByText('empty')).not.toBeNull();
  });

  it('asks for a session instead of listing orders without one', async () => {
    const fetchMock = stubFetch({ orders: [ORDER], count: 1 });
    authState.user = null;

    render(<OrdersPage />);

    expect(await screen.findByText('signedOut')).not.toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('reports a rejected session as an authentication failure', async () => {
    stubFetch({ detail: 'Not authenticated' }, 401);

    render(<OrdersPage />);

    expect(await screen.findByText('signedOut')).not.toBeNull();
  });

  it('surfaces the verbatim gateway error', async () => {
    stubFetch({ detail: 'Order service unavailable' }, 500);

    render(<OrdersPage />);

    expect(await screen.findByText('error')).not.toBeNull();
    expect(screen.getByText('Order service unavailable')).not.toBeNull();
  });
});
