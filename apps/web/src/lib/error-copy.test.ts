import { describe, expect, it } from 'vitest';

import { copyFor, directionFor, localeFromPath } from './error-copy';

describe('localeFromPath', () => {
  it('reads the locale segment the router requires', () => {
    expect(localeFromPath('/fa/about')).toBe('fa');
    expect(localeFromPath('/ar/')).toBe('ar');
    expect(localeFromPath('/ur/learn/manual/sites')).toBe('ur');
  });

  it('returns null when the path carries no locale', () => {
    expect(localeFromPath('/')).toBeNull();
    expect(localeFromPath('')).toBeNull();
  });
});

describe('copyFor', () => {
  it('returns the maintained copy for the hand-written locales', () => {
    expect(copyFor('en', 'segment').title).toBe('Something went wrong');
    expect(copyFor('fa', 'segment').title).toBe('خطایی رخ داد');
  });

  it('gives the RTL locales their own script rather than the default locale', () => {
    // Regression: the boundary used to fall back to `fa`, so an Arabic or Urdu
    // reader whose page crashed was shown a Persian error page. The boundary
    // replaces the surface they asked for, so it is the worst possible place to
    // serve the wrong language.
    expect(copyFor('ar', 'segment').title).not.toBe(copyFor('fa', 'segment').title);
    expect(copyFor('ur', 'segment').title).not.toBe(copyFor('fa', 'segment').title);
    expect(copyFor('ar', 'segment').title).toContain('حدث خطأ');
    expect(copyFor('ur', 'segment').title).toContain('خرابی');
  });

  it('falls back to English, not to Persian, for an untranslated locale', () => {
    for (const locale of ['zh', 'de', 'fr', 'it', 'ms', 'pt', 'ru', 'bn', 'hi']) {
      expect(copyFor(locale, 'segment').title).toBe(copyFor('en', 'segment').title);
    }
  });

  it('falls back rather than rendering an empty boundary for other locales', () => {
    for (const locale of ['ar', 'ur', 'zh', 'de', 'fr']) {
      const copy = copyFor(locale, 'segment');
      expect(copy.title.length).toBeGreaterThan(0);
      expect(copy.description.length).toBeGreaterThan(0);
      expect(copy.retry.length).toBeGreaterThan(0);
    }
  });

  it('falls back for an unknown or missing locale', () => {
    // No locale at all means the default, which is Persian. A locale that exists
    // in the routing table but has no hand-written string falls back to English.
    expect(copyFor(undefined, 'global').title).toBe(copyFor('fa', 'global').title);
    expect(copyFor('klingon', 'global').title).toBe(copyFor('en', 'global').title);
    expect(copyFor('zh', 'global').title).toBe(copyFor('en', 'global').title);
  });

  it('gives both boundaries the same keys so a swap cannot break the layout', () => {
    expect(Object.keys(copyFor('en', 'global')).sort()).toEqual(
      Object.keys(copyFor('en', 'segment')).sort(),
    );
  });

  it('never claims the server changed something', () => {
    // The honest wording matters: a reader must not think a write succeeded.
    expect(copyFor('en', 'segment').description).toContain('Nothing was changed');
  });
});

describe('directionFor', () => {
  it('marks the three RTL locales as RTL and everything else as LTR', () => {
    expect(directionFor('fa')).toBe('rtl');
    expect(directionFor('ar')).toBe('rtl');
    expect(directionFor('ur')).toBe('rtl');
    expect(directionFor('en')).toBe('ltr');
    expect(directionFor('zh')).toBe('ltr');
    expect(directionFor(undefined)).toBe('rtl');
  });
});
