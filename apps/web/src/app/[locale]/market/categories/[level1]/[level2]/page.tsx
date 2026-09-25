import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { MarketplaceTemplatePage } from '@/components/market/MarketplaceTemplatePage';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; level1: string; level2: string }>;
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

export default async function CategoryLevel2Page({
  params,
}: {
  params: Promise<{ locale: string; level1: string; level2: string }>;
}) {
  const { locale, level1, level2 } = await params;
  return <MarketplaceTemplatePage locale={locale} group="discovery" slug={`${level1}/${level2}`} />;
}
