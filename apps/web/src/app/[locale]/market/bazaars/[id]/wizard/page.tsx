import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { MarketplaceTemplatePage } from '@/components/market/MarketplaceTemplatePage';

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
 * The 10-step establishment flow is not served: the gateway only exposes
 * `POST /api/v1/marketplace/marketplaces` for the identity step, and the
 * signature, verification, registration and supervision steps have no endpoint
 * at all. Until each step has a real contract the route reports an explicit
 * unavailable state rather than collecting data it cannot persist.
 */
export default async function BazaarWizardPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  return <MarketplaceTemplatePage locale={locale} group="bazaars" slug={`${id}/wizard`} />;
}
