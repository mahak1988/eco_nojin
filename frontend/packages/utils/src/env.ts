import { z } from 'zod';

/**
 * Shared env schema used across both apps. Each app may extend.
 */
export const SharedEnv = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:8000'),
  VITE_MAP_STYLE_URL: z.string().url().optional(),
  VITE_SENTRY_DSN: z.string().url().optional(),
  VITE_SUPABASE_URL: z.string().url().optional(),
  VITE_SUPABASE_ANON_KEY: z.string().optional(),
  VITE_DEFAULT_LOCALE: z.enum(['en', 'fa', 'ar', 'ur']).default('fa'),
});

export type SharedEnv = z.infer<typeof SharedEnv>;

export function parseSharedEnv(source: Record<string, unknown>): SharedEnv {
  return SharedEnv.parse(source);
}