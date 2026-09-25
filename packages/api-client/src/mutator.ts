// Custom Orval mutator: a single fetch-based request function used by the
// generated API client. There is no mock layer — every call hits the real gateway.

let configuredBaseUrl: string | null = null;

export function setApiBaseUrl(url: string): void {
  configuredBaseUrl = url.replace(/\/$/, '');
}

export function getApiBaseUrl(): string {
  if (configuredBaseUrl) return configuredBaseUrl;
  if (typeof window === 'undefined') return process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000';
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';
}

export const apiRequest = async <T>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  const fullUrl = `${getApiBaseUrl()}${url}`;
  const method = (options?.method ?? 'GET').toUpperCase();
  const headers = new Headers(options?.headers);
  if (!headers.has('Accept')) headers.set('Accept', 'application/json');
  if (options?.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRF-Intent', '1');
  }

  const response = await fetch(fullUrl, {
    ...options,
    headers,
    credentials: 'same-origin',
  });

  const text = await response.text();
  let payload: unknown;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const message =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload as T;
};

export default apiRequest;
