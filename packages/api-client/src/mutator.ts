// Custom Orval mutator: a single fetch-based request function used by the
// generated API client. There is no mock layer — every call hits the real gateway.

let baseUrl = '';

export function setApiBaseUrl(url: string): void {
  baseUrl = url.replace(/\/$/, '');
}

export function getApiBaseUrl(): string {
  return baseUrl;
}

export const apiRequest = async <T>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  const fullUrl = `${baseUrl}${url}`;

  const response = await fetch(fullUrl, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options?.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...options?.headers,
    },
    credentials: 'include',
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
