import { API_BASE_PATH, API_TIMEOUT_MS } from '@eco/config';

/**
 * Standard HTTP error thrown by the API client.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly url: string,
    public readonly body: unknown,
    message?: string,
  ) {
    super(message ?? `API ${status} on ${url}`);
    this.name = 'ApiError';
  }
}

export type RequestOptions = {
  signal?: AbortSignal;
  query?: Record<string, string | number | boolean | undefined | null>;
  headers?: Record<string, string>;
  timeoutMs?: number;
};

/**
 * Fetch wrapper with base URL, JSON parsing, Zod parsing, error handling.
 *
 * The schema is validated on the boundary so callers receive typed data.
 */
export class ApiClient {
  readonly baseUrl: string;
  readonly defaultHeaders: Record<string, string>;

  constructor(opts: { baseUrl: string; defaultHeaders?: Record<string, string> }) {
    this.baseUrl = opts.baseUrl;
    this.defaultHeaders = opts.defaultHeaders ?? {};
  }

  private url(path: string, query?: RequestOptions['query']): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const fullPath = cleanPath.startsWith(API_BASE_PATH)
      ? cleanPath
      : `${API_BASE_PATH}${cleanPath}`;
    const base = `${this.baseUrl}${fullPath}`;
    if (!query) return base;
    const usp = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue;
      usp.set(k, String(v));
    }
    const qs = usp.toString();
    return qs ? `${base}?${qs}` : base;
  }

  async get<T>(path: string, schema: import('zod').ZodType<T>, opts: RequestOptions = {}): Promise<T> {
    return this.request('GET', path, undefined, schema, opts);
  }

  async post<T>(
    path: string,
    body: unknown,
    schema: import('zod').ZodType<T>,
    opts: RequestOptions = {},
  ): Promise<T> {
    return this.request('POST', path, body, schema, opts);
  }

  async put<T>(
    path: string,
    body: unknown,
    schema: import('zod').ZodType<T>,
    opts: RequestOptions = {},
  ): Promise<T> {
    return this.request('PUT', path, body, schema, opts);
  }

  async delete<T>(
    path: string,
    schema: import('zod').ZodType<T>,
    opts: RequestOptions = {},
  ): Promise<T> {
    return this.request('DELETE', path, undefined, schema, opts);
  }

  private async request<T>(
    method: string,
    path: string,
    body: unknown,
    schema: import('zod').ZodType<T>,
    opts: RequestOptions,
  ): Promise<T> {
    const ctrl = new AbortController();
    const timeout = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? API_TIMEOUT_MS);
    opts.signal?.addEventListener('abort', () => ctrl.abort());

    try {
      const res = await fetch(this.url(path, opts.query), {
        method,
        headers: {
          'content-type': 'application/json',
          accept: 'application/json',
          ...this.defaultHeaders,
          ...opts.headers,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: ctrl.signal,
      });

      const text = await res.text();
      const json: unknown = text ? JSON.parse(text) : null;

      if (!res.ok) {
        throw new ApiError(res.status, this.url(path, opts.query), json);
      }

      const parsed = schema.safeParse(json);
      if (!parsed.success) {
        throw new ApiError(
          500,
          this.url(path, opts.query),
          json,
          `Response schema mismatch for ${method} ${path}: ${parsed.error.message}`,
        );
      }
      return parsed.data;
    } finally {
      clearTimeout(timeout);
    }
  }
}

let _client: ApiClient | undefined;
export function getApiClient(): ApiClient {
  if (!_client) _client = new ApiClient({ baseUrl: 'http://localhost:8000' });
  return _client;
}

export function setApiClient(client: ApiClient): void {
  _client = client;
}

/** Inject a token (e.g. JWT) into all subsequent requests. */
export function setApiAuthToken(token: string | null): void {
  const client = getApiClient();
  if (token) {
    client.defaultHeaders['authorization'] = `Bearer ${token}`;
  } else {
    delete client.defaultHeaders['authorization'];
  }
}