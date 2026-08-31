import axios from 'axios';
import { env } from '@/lib/env';

export const apiClient = axios.create({
  baseURL: env.VITE_API_BASE_URL,
  timeout: 20000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(normalizeApiError(error));
  }
);


/**
 * Get access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('access_token');
}


/**
 * Normalize API error for consistent handling
 */
export function normalizeApiError(error: unknown): {
  message: string;
  status?: number;
  code?: string;
} {
  if (error instanceof Error) {
    return { message: error.message };
  }
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    return {
      message: (err.message as string) || 'Unknown error',
      status: err.status as number | undefined,
      code: err.code as string | undefined,
    };
  }
  return { message: String(error) };
}
