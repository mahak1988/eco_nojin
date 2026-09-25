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

export default async function BazaarWizardStep4Page({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  return <MarketplaceTemplatePage locale={locale} group="bazaars" slug={`${id}/wizard/step4`} />;
}
