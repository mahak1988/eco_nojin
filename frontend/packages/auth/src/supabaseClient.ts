/**
 * Supabase client singleton.
 *
 * Auth-flow role only uses the anon key on the client. The `supabase` object
 * is also importable by the API mutator so it can read the current session.
 *
 * If `VITE_SUPABASE_URL` is missing the client is created with a placeholder
 * so the bundle compiles. Runtime calls will fail loudly until env is set.
 */
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const PLACEHOLDER_URL = 'http://localhost:54321';
const PLACEHOLDER_ANON = 'public-anon-key-placeholder';

function resolveEnv(): { url: string; key: string } {
  if (typeof import.meta === 'undefined') {
    return { url: PLACEHOLDER_URL, key: PLACEHOLDER_ANON };
  }
  const env = (import.meta as { env?: Record<string, string | undefined> }).env ?? {};
  return {
    url: env['VITE_SUPABASE_URL'] ?? PLACEHOLDER_URL,
    key: env['VITE_SUPABASE_ANON_KEY'] ?? PLACEHOLDER_ANON,
  };
}

let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!_client) {
    const { url, key } = resolveEnv();
    _client = createClient(url, key, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }
  return _client;
}

export const supabase = getSupabase();