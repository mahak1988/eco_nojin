'use client';

import { useTranslations } from 'next-intl';

/** Absolute key of the `auth` namespace, e.g. `auth.validation.emailInvalid`. */
export type AuthMessageKey = `auth.${string}`;

const NAMESPACE = 'auth.';

/** Strips the `auth.` prefix so a scoped translator can resolve the key. */
export function toScopedAuthKey(key: AuthMessageKey): string {
  return key.startsWith(NAMESPACE) ? key.slice(NAMESPACE.length) : key;
}

/**
 * Resolves absolute `auth.*` message keys against the `auth` namespace.
 *
 * The helpers in this folder hand out absolute keys so a key can be checked
 * against the catalogues, while the components stay scoped to one namespace.
 * The `AuthMessageKey` type rejects any key that is not under `auth.`.
 */
export function useAuthMessage() {
  const t = useTranslations('auth');
  return (key: AuthMessageKey, values?: Parameters<typeof t>[1]) => t(toScopedAuthKey(key), values);
}
