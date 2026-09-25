import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { MarketplaceTemplatePage } from '@/components/market/MarketplaceTemplatePage';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
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
 * A standalone confirmation route cannot be honest: it has no order or payment
 * identifier in its params, so it cannot read the escrow record it claims to
 * confirm. The real confirmation lives in `/market/checkout`, which shows the
 * orders, payments and escrow entries the gateway returned for this session.
 */
export default async function CheckoutConfirmationPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return <MarketplaceTemplatePage locale={locale} group="purchase" slug="confirmation" />;
}
