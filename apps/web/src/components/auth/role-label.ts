import type { GlobalRole } from '@/lib/auth/roles';
import { isGlobalRole } from '@/lib/auth/roles';
import type { AccountLanguage } from './validation';
import { ACCOUNT_LANGUAGES } from './validation';

export const AUTH_ROLE_KEYS = [
  'auth.roles.regular',
  'auth.roles.tourist',
  'auth.roles.farmer',
  'auth.roles.advisor',
  'auth.roles.researcher',
  'auth.roles.organization',
  'auth.roles.admin',
  'auth.roles.security_admin',
  'auth.roles.content_admin',
  'auth.roles.user_admin',
] as const;

export type AuthRoleKey = (typeof AUTH_ROLE_KEYS)[number];

const ROLE_KEYS: Record<GlobalRole, AuthRoleKey> = {
  regular: 'auth.roles.regular',
  tourist: 'auth.roles.tourist',
  farmer: 'auth.roles.farmer',
  advisor: 'auth.roles.advisor',
  researcher: 'auth.roles.researcher',
  organization: 'auth.roles.organization',
  admin: 'auth.roles.admin',
  security_admin: 'auth.roles.security_admin',
  content_admin: 'auth.roles.content_admin',
  user_admin: 'auth.roles.user_admin',
};

/** Unknown or future roles resolve to `null` so the raw value stays visible. */
export function roleLabelKey(role: string | null | undefined): AuthRoleKey | null {
  if (typeof role !== 'string' || !isGlobalRole(role)) return null;
  return ROLE_KEYS[role];
}

export const AUTH_LANGUAGE_KEYS = [
  'auth.languages.fa',
  'auth.languages.en',
  'auth.languages.ar',
] as const;

export type AuthLanguageKey = (typeof AUTH_LANGUAGE_KEYS)[number];

const LANGUAGE_KEYS: Record<AccountLanguage, AuthLanguageKey> = {
  fa: 'auth.languages.fa',
  en: 'auth.languages.en',
  ar: 'auth.languages.ar',
};

export function accountLanguageKey(language: string | null | undefined): AuthLanguageKey | null {
  if (typeof language !== 'string') return null;
  const match = ACCOUNT_LANGUAGES.find((value) => value === language);
  return match ? LANGUAGE_KEYS[match] : null;
}
