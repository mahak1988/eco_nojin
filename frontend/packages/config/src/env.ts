import { z } from 'zod';

const EnvSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:8000'),
  VITE_MAP_STYLE_URL: z.string().url().optional(),
  VITE_SENTRY_DSN: z.string().url().optional(),
  VITE_SUPABASE_URL: z.string().url().optional(),
  VITE_SUPABASE_ANON_KEY: z.string().optional(),
  VITE_DEFAULT_LOCALE: z.enum(['en', 'fa', 'ar', 'ur']).default('fa'),
  VITE_ENABLE_DEVTOOLS: z
    .union([z.literal('true'), z.literal('false')])
    .transform((v) => v === 'true')
    .optional(),
});

export type AppEnv = z.infer<typeof EnvSchema>;

export function loadAppEnv(source: Record<string, unknown>): AppEnv {
  return EnvSchema.parse(source);
}