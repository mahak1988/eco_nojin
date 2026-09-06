import { API_BASE_PATH } from '@eco/config';
import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';

const BASE_URL =
  (typeof import.meta !== 'undefined' &&
    (import.meta as { env?: Record<string, string | undefined> }).env?.['VITE_API_URL']) ||
  'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}${API_BASE_PATH}`,
  timeout: 30_000,
  headers: { 'content-type': 'application/json' },
});

// Lazy-import supabase so apps that don't use auth don't need it installed.
let supabaseModule: typeof import('@eco/auth/supabaseClient') | null = null;
async function getSupabaseModule(): Promise<typeof import('@eco/auth/supabaseClient') | null> {
  if (supabaseModule) return supabaseModule;
  try {
    supabaseModule = await import('@eco/auth/supabaseClient');
    return supabaseModule;
  } catch {
    return null;
  }
}

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const mod = await getSupabaseModule();
  if (mod) {
    try {
      const { data } = await mod.supabase.auth.getSession();
      const token = data.session?.access_token;
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
        return config;
      }
    } catch {
      // ignore — fall through to legacy token
    }
  }
  // Fallback to localStorage token (legacy Zustand store)
  const token = typeof window !== 'undefined' ? window.localStorage.getItem('eco_token') : null;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      window.localStorage.removeItem('eco_token');
      const mod = await getSupabaseModule();
      if (mod) {
        try {
          await mod.supabase.auth.signOut();
        } catch {
          // ignore
        }
      }
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Orval-compatible mutator signature.
 */
export const customAxios = <T>(config: AxiosRequestConfig): Promise<T> => {
  return apiClient.request<T>(config).then((res: AxiosResponse<T>) => res.data);
};

/**
 * Push or clear the bearer token used by {@link apiClient}.
 */
export function setApiAuthToken(token: string | null): void {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
}

export default customAxios;