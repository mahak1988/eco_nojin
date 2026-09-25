import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { MarketplaceTemplatePage } from '@/components/market/MarketplaceTemplatePage';
import { MARKETPLACE_ROUTE_GROUPS } from '@/lib/marketplace-routes';

export const dynamic = 'force-dynamic';

function resolveGroup(segments: string[]) {
  const [base, slug] = segments;
  const group = MARKETPLACE_ROUTE_GROUPS.find((candidate) => candidate.base === base);
  if (!group || !slug) return null;
  const prefix = `${group.prefix}-`;
  if (!slug.startsWith(prefix)) return null;
  const index = Number(slug.slice(prefix.length));
  if (!Number.isInteger(index) || index < 1 || index > group.count) return null;
  return { group, slug };
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; segments: string[] }>;
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

export default async function MarketplaceGeneratedPage({
  params,
}: {
  params: Promise<{ locale: string; segments: string[] }>;
}) {
  const { locale, segments } = await params;
  const resolved = resolveGroup(segments);
  if (!resolved) notFound();
  return <MarketplaceTemplatePage locale={locale} group={resolved.group.id} slug={resolved.slug} />;
}
