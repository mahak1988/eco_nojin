import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { LanguageProvider } from '../i18n/LanguageContext';
import { useBilingual, useBilingualList } from '../lib/i18n';

const STORAGE_KEY = 'eco_nojin_lang';

function mockLang(lang: 'fa' | 'en') {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
    if (key === STORAGE_KEY) return lang;
    return null;
  });
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});
  Object.defineProperty(document, 'cookie', {
    value: `lang=${lang}`,
    writable: true,
    configurable: true,
  });
}

function renderWithLang(hook: () => unknown, lang: 'fa' | 'en' = 'fa') {
  mockLang(lang);
  return renderHook(hook, {
    wrapper: ({ children }) => <LanguageProvider>{children}</LanguageProvider>,
  });
}

describe('useBilingual (backward-compatible wrapper)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns Persian value when lang is fa', () => {
    const { result } = renderWithLang(() => useBilingual('فارسی', 'English'));
    expect(result.current).toBe('فارسی');
  });

  it('returns English value when lang is en', () => {
    const { result } = renderWithLang(() => useBilingual('فارسی', 'English'), 'en');
    expect(result.current).toBe('English');
  });
});

describe('useBilingualList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns items as-is for active language', () => {
    const items = [
      { fa: 'فارسی', en: 'Persian' },
      { fa: 'عربی', en: 'Arabic' },
    ];
    const { result } = renderWithLang(() => useBilingualList(items));
    expect(result.current).toEqual(items);
  });

  it('returns empty array for empty input', () => {
    const { result } = renderWithLang(() => useBilingualList([]));
    expect(result.current).toEqual([]);
  });
});
