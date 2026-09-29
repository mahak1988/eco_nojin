import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { MarketMap } from '@/components/MarketMap';
import { apiGet } from '@/lib/api/client';
import type { BazaarType } from '@/types/bazaar-types';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.template');

  return {
    title: t('title'),
    description: t('description'),
    robots: { index: false, follow: true },
  };
}

/**
 * The bazaar boundary map, rendered by `MarketMap`.
 *
 * `MarketMap` was written for this route and then never mounted, so the page
 * delegated to the generic template and the map work was dead. The component
 * needs the marketplace list, which the gateway publishes, so the page reads it
 * and passes it through; the component itself never fetches.
 *
 * The shape is read through `readRows` because the gateway's contract for this
 * path is not a published array field. A mismatch therefore renders the empty
 * state naming the path, rather than a blank map that looks like "no markets".
 */
async function readRows(result: Awaited<ReturnType<typeof apiGet>>): Promise<BazaarType[]> {
  if (!result.ok || typeof result.data !== 'object' || result.data === null) return [];
  for (const value of Object.values(result.data as Record<string, unknown>)) {
    if (Array.isArray(value)) return value as BazaarType[];
  }
  return [];
}

export default async function BazaarMapPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const result = await apiGet<Record<string, unknown>>('/api/v1/marketplace/marketplaces');
  const marketplaces = await readRows(result);

  return (
    <main id="main-content" className="min-h-dvh">
      <MarketMap locale={locale} bazaars={marketplaces} />
    </main>
  );
}
