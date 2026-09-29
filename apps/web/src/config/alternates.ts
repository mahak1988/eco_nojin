import { SITE_URL } from '@/config/site';
import { locales } from '@/i18n/routing';

/**
 * Build the `alternates.languages` map that every translated page must declare.
 *
 * Fifty-three public pages were emitting a two-locale cluster — `fa` and `en`
 * only — from a hand-written `alternates` object, while the root layout emitted
 * all fourteen from the shared locale list. Search engines therefore received two
 * conflicting hreflang clusters per page, and eleven of the fourteen official
 * languages were never advertised as having a version of the page at all.
 *
 * Centralising it here means a new locale is advertised everywhere at once: the
 * list has one source, and `check:site-url` plus the locale-parity gate already
 * cover the inputs.
 *
 * @param path Absolute path without the locale prefix, e.g. `/public/why`.
 * @param localesFor Override the locale set, for pages that are not yet
 *   translated in every language.
 */
export function languageAlternates(
  path: string,
  localesFor: readonly string[] = locales,
): Record<string, string> {
  const normalised = path.startsWith('/') ? path : `/${path}`;
  const withoutTrailingSlash = normalised.replace(/\/+$/, '');
  return Object.fromEntries(
    localesFor.map((locale) => [locale, `${SITE_URL}/${locale}${withoutTrailingSlash}`]),
  );
}

/** Canonical URL for a localized path, used for `alternates.canonical`. */
export function canonicalFor(locale: string, path: string): string {
  const normalised = path.startsWith('/') ? path : `/${path}`;
  return `${SITE_URL}/${locale}${normalised.replace(/\/+$/, '')}`;
}
