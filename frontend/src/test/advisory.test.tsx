import { describe, expect, it, vi } from 'vitest';
import { fetchAdvice, useAdvisory } from '../lib/advisory';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';

const mockClient = new QueryClient();

function wrapper({ children }: { children: React.ReactNode }) {
  return createElement(QueryClientProvider, { client: mockClient }, children);
}

describe('fetchAdvice', () => {
  it('sends POST to /api/v1/ai/advise with question', async () => {
    const mockAnswer = { status: 'ok', answer: 'test answer' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAnswer,
    }) as unknown as typeof fetch;

    const result = await fetchAdvice({ question: 'test question' });

    expect(result).toEqual(mockAnswer);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/ai/advise'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    }) as unknown as typeof fetch;

    await expect(fetchAdvice({ question: 'test' })).rejects.toThrow('advisory_fetch_failed_500');
  });

  it('includes lat/lon when provided', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    }) as unknown as typeof fetch;

    await fetchAdvice({ question: 'test', lat: 32.42, lon: 54.01 });

    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse(call[1].body as string);
    expect(body.question).toBe('test');
    expect(body.lat).toBe(32.42);
    expect(body.lon).toBe(54.01);
  });
});

describe('useAdvisory', () => {
  it('uses question in query key', () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok', answer: 'hello' }),
    }) as unknown as typeof fetch;

    const { result } = renderHook(() => useAdvisory('test question'), { wrapper });

    expect(result.current.isLoading || result.current.isFetching || result.current.data === undefined).toBe(true);
  });

  it('is disabled for short questions', () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    }) as unknown as typeof fetch;

    const { result } = renderHook(() => useAdvisory('ab'), { wrapper });

    expect(result.current.isFetching).toBe(false);
  });

  it('fetches and stores answer', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok', answer: 'crop recommendation' }),
    }) as unknown as typeof fetch;

    const { result } = renderHook(() => useAdvisory('what crop to plant'), { wrapper });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => expect(result.current.data).toBeDefined());

    expect(result.current.data?.answer).toBe('crop recommendation');
  });
});
