import { z } from 'zod';

const apiBaseUrlSchema = z
  .string()
  .trim()
  .min(1)
  .transform((value) => value.replace(/\/+$/, ''))
  .refine(
    (value) =>
      value.startsWith('/') ||
      (process.env.NODE_ENV !== 'production' &&
        (() => {
          try {
            new URL(value);
            return true;
          } catch {
            return false;
          }
        })()),
    { message: 'NEXT_PUBLIC_API_BASE_URL must be same-origin path or a development URL' },
  );

export const publicEnv = {
  apiBaseUrl: apiBaseUrlSchema.parse(process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api'),
};

export function resolveApiUrl(path: string): string {
  if (typeof window === 'undefined') {
    const target = (process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000').replace(/\/+$/, '');
    return `${target}${path}`;
  }
  return `${publicEnv.apiBaseUrl}${path}`;
}
