import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { CatalogPage } from '@/components/catalog/CatalogPage';
import { SITE_URL as BASE_URL } from '@/config/site';
import {
  catalogFallbackParams,
  getCatalogEntryForSlug,
  resolveRobots,
} from '@/lib/domains/page-catalog';

export const dynamic = 'force-dynamic';

/**
 * Static params for the catalog catch-all.
 *
 * `catalogFallbackParams()` returns one param per registry surface that has no
 * page of its own, and it drops two classes of path on purpose:
 *
 *   - every path already served by a real `page.tsx`, so this route can never
 *     claim a second route for one URL;
 *   - every path under `/market`, which the existing marketplace catch-all owns
 *     together with the 444 pages declared in `lib/marketplace-routes.ts`.
 *
 * Next still prefers a concrete or dynamic sibling over a catch-all, so the two
 * filters are a correctness guard rather than a routing workaround: without them
 * a param could match two route files, which is what produces a duplicate static
 * param report. `dynamicParams` is left at its default because the locale layout
 * renders dynamically; an unknown slug is rejected by the page itself.
 */
export function generateStaticParams(): { slug: string[] }[] {
  return catalogFallbackParams();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string[] }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const entry = getCatalogEntryForSlug(slug);
  // An unregistered slug is not a catalog surface. Rejecting it here as well as
  // in the page keeps the response a real 404 instead of a 200 that only claims
  // one in its body, and stops the fallback title from leaking onto it.
  if (!entry) notFound();

  const t = await getTranslations();
  const path = entry.path === '/' ? '' : entry.path;
  const endpoint = entry.endpoint ?? t('statusLine.unavailable');

  return {
    title: t('market.template.unavailableTitle'),
    description: `${t('market.template.unavailableDescription')} ${t('statusPage.endpoint')}: ${endpoint}.`,
    robots: resolveRobots(entry.status),
    alternates: {
      canonical: `${BASE_URL}/${locale}${path}`,
    },
  };
}

export default async function CatalogFallbackPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string[] }>;
}) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const entry = getCatalogEntryForSlug(slug);
  // Anything already routed keeps its own page; this route answers only for the
  // surfaces the registry declares without a route.
  if (entry?.renderedBy !== 'catalog-catchall') notFound();
  return <CatalogPage locale={locale} entry={entry} />;
}
