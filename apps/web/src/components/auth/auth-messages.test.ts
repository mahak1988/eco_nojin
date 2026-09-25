import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { AUTH_ERROR_KEYS, errorDetail, toAuthErrorKey } from './errors';
import { isMachineTranslated } from './locale-meta';
import { AUTH_LANGUAGE_KEYS, AUTH_ROLE_KEYS, accountLanguageKey, roleLabelKey } from './role-label';
import { toScopedAuthKey } from './useAuthMessage';
import { AUTH_VALIDATION_KEYS } from './validation';

const LOCALES = [
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'ru',
  'zh',
  'bn',
] as const;

type Catalogue = Record<string, unknown>;

const CONTRACT_KEYS = [
  ...AUTH_VALIDATION_KEYS,
  ...AUTH_ERROR_KEYS,
  ...AUTH_ROLE_KEYS,
  ...AUTH_LANGUAGE_KEYS,
];

function loadCatalogue(locale: string): Catalogue {
  const file = path.join(process.cwd(), 'messages', `${locale}.json`);
  const raw = readFileSync(file, 'utf8').replace(/^﻿/, '');
  return JSON.parse(raw) as Catalogue;
}

function resolveKey(catalogue: Catalogue, key: string): unknown {
  return key.split('.').reduce<unknown>((node, segment) => {
    if (typeof node !== 'object' || node === null) return undefined;
    return (node as Record<string, unknown>)[segment];
  }, catalogue);
}

describe('auth message-key contract', () => {
  it('ships every key emitted by the auth helpers in all 14 catalogues', () => {
    for (const locale of LOCALES) {
      const catalogue = loadCatalogue(locale);
      for (const key of CONTRACT_KEYS) {
        const value = resolveKey(catalogue, key);
        expect(typeof value, `${locale} is missing ${key}`).toBe('string');
      }
    }
  });

  it('serves non-fa/en auth copy from the English keys', () => {
    const english = loadCatalogue('en');
    for (const locale of LOCALES) {
      if (locale === 'en' || locale === 'fa') continue;
      const catalogue = loadCatalogue(locale);
      for (const key of CONTRACT_KEYS) {
        expect(resolveKey(catalogue, key), `${locale}.${key}`).toBe(resolveKey(english, key));
      }
    }
  });

  it('keeps the machine-translation flag honest', () => {
    expect(isMachineTranslated(loadCatalogue('fa'))).toBe(false);
    expect(isMachineTranslated(loadCatalogue('en'))).toBe(false);
    expect(isMachineTranslated(loadCatalogue('de'))).toBe(true);
    expect(isMachineTranslated(undefined)).toBe(false);
    expect(isMachineTranslated({ meta: { machineTranslated: 'yes' } })).toBe(false);
  });
});

describe('auth message keys', () => {
  it('resolves absolute keys against the scoped auth namespace', () => {
    expect(toScopedAuthKey('auth.validation.emailInvalid')).toBe('validation.emailInvalid');
    expect(toScopedAuthKey('auth.common.provenance.heading')).toBe('common.provenance.heading');
  });
});

describe('BFF failure mapping', () => {
  it('maps known BFF details to message keys', () => {
    expect(toAuthErrorKey(new Error('Missing CSRF intent header'))).toBe('auth.errors.forbidden');
    expect(toAuthErrorKey(new Error('Invalid request payload'))).toBe('auth.errors.invalidPayload');
    expect(toAuthErrorKey(new Error('Backend unavailable'))).toBe('auth.errors.unavailable');
    expect(toAuthErrorKey(new Error('Backend request timed out'))).toBe('auth.errors.timeout');
  });

  it('falls back for upstream details and honours a caller fallback', () => {
    expect(toAuthErrorKey(new Error('Incorrect email or password'))).toBe('auth.errors.rejected');
    expect(toAuthErrorKey(new Error('boom'), 'auth.errors.signOutFailed')).toBe(
      'auth.errors.signOutFailed',
    );
    expect(toAuthErrorKey(undefined)).toBe('auth.errors.rejected');
  });

  it('exposes the raw server detail only as supplementary text', () => {
    expect(errorDetail(new Error('Incorrect email or password'))).toBe(
      'Incorrect email or password',
    );
    expect(errorDetail(new Error('   '))).toBeUndefined();
    expect(errorDetail('plain string')).toBeUndefined();
  });
});

describe('role and account language labels', () => {
  it('labels every global role and leaves unknown values to the caller', () => {
    expect(roleLabelKey('farmer')).toBe('auth.roles.farmer');
    expect(roleLabelKey('security_admin')).toBe('auth.roles.security_admin');
    expect(roleLabelKey('wizard')).toBeNull();
    expect(roleLabelKey(undefined)).toBeNull();
  });

  it('labels only the languages the register contract accepts', () => {
    expect(accountLanguageKey('fa')).toBe('auth.languages.fa');
    expect(accountLanguageKey('ar')).toBe('auth.languages.ar');
    expect(accountLanguageKey('de')).toBeNull();
    expect(accountLanguageKey(null)).toBeNull();
  });
});
