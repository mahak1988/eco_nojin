import { NextRequest, NextResponse } from 'next/server';
import { ZodError } from 'zod';
import { getApiProxyTarget, getPublicAppUrl } from '@/lib/config/server-env';

const unsafeMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export class BffError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'BffError';
  }
}

export function assertBffRequest(request: NextRequest): void {
  if (!unsafeMethods.has(request.method.toUpperCase())) return;
  const expectedOrigin = getPublicAppUrl().origin;
  if (request.headers.get('origin') !== expectedOrigin) {
    throw new BffError(403, 'Invalid request origin');
  }
  if (request.headers.get('x-csrf-intent') !== '1') {
    throw new BffError(403, 'Missing CSRF intent header');
  }
  const fetchSite = request.headers.get('sec-fetch-site');
  if (fetchSite && fetchSite !== 'same-origin') {
    throw new BffError(403, 'Cross-site mutation rejected');
  }
}

export async function backendRequest(
  path: string,
  init: RequestInit & { accessToken?: string } = {},
): Promise<Response> {
  const timeoutSignal = AbortSignal.timeout(15_000);
  const signal = init.signal ? AbortSignal.any([init.signal, timeoutSignal]) : timeoutSignal;
  const headers = new Headers(init.headers);
  if (init.accessToken) headers.set('Authorization', `Bearer ${init.accessToken}`);
  return fetch(`${getApiProxyTarget()}${path}`, {
    ...init,
    headers,
    signal,
    cache: 'no-store',
  });
}

export function backendError(status: number, payload: unknown): BffError {
  const detail =
    typeof payload === 'object' && payload !== null && 'detail' in payload
      ? String((payload as { detail: unknown }).detail)
      : `Backend request failed with status ${status}`;
  return new BffError(status, detail);
}

export async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function errorResponse(error: unknown): NextResponse {
  if (error instanceof BffError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  if (error instanceof ZodError) {
    return NextResponse.json({ error: 'Invalid request payload' }, { status: 422 });
  }
  if (error instanceof Error && (error.name === 'AbortError' || error.name === 'TimeoutError')) {
    return NextResponse.json({ error: 'Backend request timed out' }, { status: 504 });
  }
  if (error instanceof TypeError && error.message.includes('fetch failed')) {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
  return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
}
