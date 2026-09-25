import { z } from 'zod';

const urlSchema = z.string().trim().url();

export function getApiProxyTarget(): string {
  return urlSchema.parse(process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000');
}

export function getPublicAppUrl(): URL {
  const parsed = urlSchema.parse(process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3001');
  const url = new URL(parsed);
  if (process.env.NODE_ENV === 'production' && url.protocol !== 'https:') {
    throw new Error('NEXT_PUBLIC_APP_URL must use HTTPS in production');
  }
  return new URL(url);
}

export function getRedisUrl(): string | null {
  const value = process.env.REDIS_URL?.trim();
  if (!value) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('REDIS_URL is required in production');
    }
    return null;
  }
  return urlSchema.parse(value);
}

export function getSessionTtlSeconds(): number {
  const value = z.coerce
    .number()
    .int()
    .positive()
    .safe()
    .parse(process.env.SESSION_TTL_SECONDS ?? 28_800);
  return value;
}
