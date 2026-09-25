/**
 * BFF failures reach the browser as a plain `Error` carrying the server
 * detail. Known BFF details are mapped to message keys; anything else
 * (rejected credentials, duplicate account, upstream detail) falls back to a
 * page-specific key so no raw server string becomes interface copy.
 */
export const AUTH_ERROR_KEYS = [
  'auth.errors.forbidden',
  'auth.errors.invalidPayload',
  'auth.errors.unavailable',
  'auth.errors.timeout',
  'auth.errors.unknown',
  'auth.errors.rejected',
  'auth.errors.signOutFailed',
] as const;

export type AuthErrorKey = (typeof AUTH_ERROR_KEYS)[number];

const BFF_ERROR_KEYS: Readonly<Record<string, AuthErrorKey>> = {
  'Invalid request origin': 'auth.errors.forbidden',
  'Missing CSRF intent header': 'auth.errors.forbidden',
  'Cross-site mutation rejected': 'auth.errors.forbidden',
  'Invalid request payload': 'auth.errors.invalidPayload',
  'Backend unavailable': 'auth.errors.unavailable',
  'Backend request timed out': 'auth.errors.timeout',
  'Internal server error': 'auth.errors.unknown',
};

export function toAuthErrorKey(
  error: unknown,
  fallback: AuthErrorKey = 'auth.errors.rejected',
): AuthErrorKey {
  const message = error instanceof Error ? error.message : typeof error === 'string' ? error : '';
  return BFF_ERROR_KEYS[message] ?? fallback;
}

/** Locale-neutral server detail, shown as supplementary information only. */
export function errorDetail(error: unknown): string | undefined {
  if (!(error instanceof Error)) return undefined;
  const detail = error.message.trim();
  return detail.length > 0 ? detail : undefined;
}
