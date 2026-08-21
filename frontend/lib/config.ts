/**
 * Configurable API base URL for the Eco Nojin frontend.
 *
 * Reads NEXT_PUBLIC_API_URL at build time (Next.js inlines public env vars
 * into the client bundle). Falls back to the local FastAPI backend default.
 *
 * Example:
 *   NEXT_PUBLIC_API_URL=https://api.example.com pnpm build
 */
export const API_BASE: string =
  (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

/** Absolute URL helper for API endpoints (avoids duplicated prefixes). */
export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}
