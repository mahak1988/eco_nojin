import { describe, expect, it } from 'vitest';
import { defaultLocale, isRtl, locales, rtlLocales } from './routing';

describe('i18n routing contract (master plan Phase 0)', () => {
  it('exposes exactly the 14 official platform locales', () => {
    expect([...locales].sort()).toEqual(
      ['ar', 'bn', 'de', 'en', 'es', 'fa', 'fr', 'hi', 'it', 'ms', 'pt', 'ru', 'ur', 'zh'].sort(),
    );
  });

  it('defaults to Persian and keeps fa RTL', () => {
    expect(defaultLocale).toBe('fa');
    expect(isRtl('fa')).toBe(true);
    expect(isRtl('ar')).toBe(true);
    expect(isRtl('ur')).toBe(true);
  });

  it('marks LTR locales correctly', () => {
    expect(rtlLocales).toHaveLength(3);
    expect(isRtl('en')).toBe(false);
    expect(isRtl('de')).toBe(false);
    expect(isRtl('zh')).toBe(false);
  });
});
