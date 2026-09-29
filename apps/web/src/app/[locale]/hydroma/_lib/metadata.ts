import type { Metadata } from 'next';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

/**
 * Per-locale metadata for a HyDroMa page.
 *
 * `check-page-meta.mjs` fails three shapes of heading metadata, and all three
 * have been produced here before: an inline `{fa, en}` dictionary, a hand-written
 * two-locale hreflang cluster, and a bare identifier concatenated onto the locale
 * inside a URL — which renders `https://app.eco-nojin.org/faROUTE` and sends every
 * share card to a path that does not exist. So the page's own route goes through
 * `canonicalFor` / `languageAlternates`, and the Open Graph URL interpolates it
 * explicitly.
 *
 * Titles and descriptions arrive already resolved, from `hydroma.*` in
 * `src/i18n/fragments/hydroma.json`. This subtree does not read `pageMeta.*`:
 * that namespace is generated and owned elsewhere, and a hand-written entry there
 * would be overwritten by the next generator run.
 */
export function hydromaMetadata({
  locale,
  route,
  title,
  description,
}: {
  locale: string;
  /** Path without the locale prefix, e.g. `/hydroma/soil`. */
  route: string;
  title: string;
  description: string;
}): Metadata {
  return {
    title,
    description,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${route}`,
      title,
      description,
    },
    alternates: {
      canonical: canonicalFor(locale, route),
      languages: languageAlternates(route),
    },
  };
}
