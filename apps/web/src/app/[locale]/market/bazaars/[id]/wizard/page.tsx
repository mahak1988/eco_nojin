import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { BazaarEstablishmentWizard } from '@/components/BazaarEstablishmentWizard';

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
 * The 10-step establishment flow renders through `BazaarEstablishmentWizard`.
 *
 * That component was written for this route and then never mounted: the page
 * delegated to the generic `MarketplaceTemplatePage` instead, so ten step routes
 * and a purpose-built renderer existed with nothing connecting them. The wizard
 * is the better renderer here because it names the ten steps and which of them
 * have a contract, where the generic page only says the route is unavailable.
 *
 * The flow itself is still unserved: the gateway exposes
 * `POST /api/v1/marketplace/marketplaces` for the identity step only, and the
 * signature, verification, registration and supervision steps have no endpoint.
 * The wizard reports that explicitly and posts nothing.
 */
export default async function BazaarWizardPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale } = await params;
  return (
    <main id="main-content" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <BazaarEstablishmentWizard locale={locale} />
      </div>
    </main>
  );
}
