import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'تأیید نهایی', en: 'Confirmation' };
  const descriptions: Record<string, string> = {
    fa: 'تأیید سفارش و قفل اسکرو',
    en: 'Confirm order and lock escrow',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market/checkout/confirmation`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/market/checkout/confirmation`,
      languages: {
        fa: `${BASE_URL}/fa/market/checkout/confirmation`,
        en: `${BASE_URL}/en/market/checkout/confirmation`,
      },
    },
  };
}

export default async function ConfirmationPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.confirmation');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source="/api/v1/marketplace/payments"
          label={t('provenanceLabel')}
          verified={false}
        >
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Final review', 'Escrow lock', 'Transaction key generated']}
          limits={['Irreversible after confirm', 'Funds locked 14 days', 'Dispute window opens']}
          next={['Funds transferred to escrow', 'Seller notified', 'Tracking begins']}
          evidenceLabel="Evidence"
          limitsLabel="Limits"
          nextLabel="Next"
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <div className="space-y-4">
          <div className="bg-forest/5 border border-forest/20 rounded-lg p-6 text-center">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-forest mb-2">{t('orderConfirmed')}</h2>
            <p className="text-ink-soft">{t('confirmationDesc')}</p>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('transactionKey')}</span>
              <code className="font-mono text-forest">{t('confirmationDesc')}</code>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('escrowAmount')}</span>
              <span className="font-bold text-forest">—</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('releaseCondition')}</span>
              <span className="text-ink-soft">{t('deliveryConfirmed')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('disputeWindow')}</span>
              <span className="text-ink-soft">—</span>
            </div>
          </div>

          <Button
            variant="primary"
            className="w-full mt-6"
            onClick={() => (window.location.href = `/${locale}/market/orders`)}
          >
            {t('viewOrders')}
          </Button>
        </div>
      </section>
    </main>
  );
}
