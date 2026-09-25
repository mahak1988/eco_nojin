import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiGet, apiPost, createIdempotencyKey, setApiBaseUrl } from './client';

describe('API client foundation', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setApiBaseUrl('/api');
  });

  it('supports an explicit API base and adds a request id', async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );
    vi.stubGlobal('fetch', fetchMock);
    setApiBaseUrl('https://api.example.test/');

    const result = await apiGet<{ ok: boolean }>('/health');

    expect(result.ok).toBe(true);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(url).toBe('https://api.example.test/health');
    expect(headers.get('X-Request-ID')).toBeTruthy();
    expect(init.credentials).toBe('same-origin');
  });

  it('preserves an idempotency key on financial posts', async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify({ ok: true }), { status: 201 }),
    );
    vi.stubGlobal('fetch', fetchMock);
    const idempotencyKey = createIdempotencyKey();

    const result = await apiPost<{ ok: boolean }>(
      '/api/v1/marketplace/payments',
      { amount: 100 },
      {
        headers: { 'Idempotency-Key': idempotencyKey },
      },
    );

    expect(result.ok).toBe(true);
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).get('Idempotency-Key')).toBe(idempotencyKey);
    expect(new Headers(init.headers).get('X-CSRF-Intent')).toBe('1');
  });
});
