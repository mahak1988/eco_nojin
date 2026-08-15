/**
 * HTTP client with JWT authentication.
 * Automatically attaches Authorization header when token is present.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const token = getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
    
    let data: any;
    const text = await response.text();
    try { data = JSON.parse(text); } catch { data = text; }
    
    if (!response.ok) {
      const msg = data?.detail || data?.message || `HTTP ${response.status}`;
      return { success: false, error: msg, status: response.status };
    }
    return { success: true, data, status: response.status };
  } catch (err: any) {
    return { success: false, error: err.message || 'Network error' };
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body: any) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(endpoint: string, body: any) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};

export { API_BASE };
