import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const TX_KEY = 'TXN-A7F3K9-20241210-143022';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کلید تراکنش', en: 'Transaction Key' };
  const descriptions: Record<string, string> = { fa: 'کلید یکتای تراکنش برای ردیابی', en: 'Unique transaction key for tracking' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/transaction-key`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/transaction-key`, languages: { fa: `${BASE_URL}/fa/market/checkout/transaction-key`, en: `${BASE_URL}/en/market/checkout/transaction-key` } },
  };
}

export default async function TransactionKeyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.transactionKey');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Transaction Engine" label={t('provenanceLabel')} verified={true} method="PQ-signed" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['PQ-signed key', 'Immutable on-chain', 'Shareable for tracking']}
          limits={['Key cannot be regenerated', 'Store securely', 'Valid for 180 days']}
          next={['Fund escrow', 'Share with seller', 'Monitor status']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy" className="text-center">
          <h2 className="text-xl font-semibold text-ink mb-4">{t('yourTransactionKey')}</h2>
          <div className="bg-surface p-6 rounded-lg border border-line mb-4">
            <code className="text-xl font-mono text-forest break-all">{TX_KEY}</code>
          </div>
          <div className="space-y-2 text-sm text-ink-soft">
            <p>{t('keyInfo1')}</p>
            <p>{t('keyInfo2')}</p>
            <p>{t('keyInfo3')}</p>
          </div>
          <Button variant="primary" className="w-full mt-6" onClick={() => navigator.clipboard.writeText(TX_KEY)}>
            {t('copyKey')}
          </Button>
          <Button variant="ghost" className="w-full mt-3" onClick={() => window.location.href = `/${locale}/market/checkout/ecowallet`}>
            {t('fundEscrow')}
          </Button>
        </Card>

        <ProvenanceStamp source="Transaction Engine" verified={true} method="PQ-signed" timestamp="2024-12-10" label={t('provenanceLabel')} className="mt-6" />
      </section>
    </main>
  );
}