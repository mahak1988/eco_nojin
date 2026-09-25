import { afterEach, describe, expect, it, vi } from 'vitest';
import { setApiBaseUrl } from './client';
import { openDispute, settleOrder } from './escrow';

describe('escrow API boundary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('http://127.0.0.1:8000');
  });

  it('uses idempotent POST requests for financial transitions', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ order_id: 'order-1', state: 'disputed' }), { status: 200 }),
    );
    vi.stubGlobal('fetch', fetchMock);
    setApiBaseUrl('https://api.example.test');

    await openDispute('order-1');
    await settleOrder('order-1');

    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const [, init] of fetchMock.mock.calls as unknown as Array<[string, RequestInit]>) {
      expect(init.method).toBe('POST');
      expect(new Headers(init.headers).get('Idempotency-Key')).toBeTruthy();
    }
  });
});
