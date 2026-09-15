/** API client for React Native — mirrors frontend/lib/api.ts patterns. */

/** Returns the API base URL for the mobile app. */
export function getApiBase(): string {
  const envBase = process.env.EXPO_PUBLIC_API_BASE_URL ?? '';
  if (envBase && /^https?:\/\//.test(envBase.trim())) return envBase.trim().replace(/\/$/, '');
  return '';
}

/** Generic fetch wrapper with error handling. */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${getApiBase()}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
    },
  });
  if (!response.ok) {
    throw new Error(`api_request_failed_${response.status}`);
  }
  return response.json() as Promise<T>;
}

/** Get authenticated request headers if token available. */
export function getAuthHeaders(): Record<string, string> {
  try {
    const token = ''; // Would come from SecureStore in production
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {
    /* no token */
  }
  return {};
}

/** Subscribe newsletter from mobile. */
export async function subscribeNewsletter(email: string, locale: string): Promise<{ ok: boolean; already?: boolean }> {
  return apiFetch('/api/v1/newsletter/subscribe', {
    method: 'POST',
    body: JSON.stringify({ email, locale }),
  });
}

/** Fetch advisory advice (AI farming advice). */
export async function fetchAdvice(question: string, lat?: number, lon?: number): Promise<{ answer: string; evidence?: unknown[]; metrics?: Record<string, number> }> {
  return apiFetch('/api/v1/ai/advise', {
    method: 'POST',
    body: JSON.stringify({ question, lat, lon }),
  });
}

/** List marketplace products from mobile. */
export async function listMarketplaceProducts(category?: string, limit = 50): Promise<{ products: unknown[]; count: number }> {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('limit', String(limit));
  return apiFetch(`/api/v1/marketplace/products?${params.toString()}`);
}

/** List IoT devices from mobile. */
export async function listIoTDevices(limit = 50): Promise<{ devices: unknown[]; count: number }> {
  return apiFetch(`/api/v1/iot/devices?limit=${limit}`);
}
