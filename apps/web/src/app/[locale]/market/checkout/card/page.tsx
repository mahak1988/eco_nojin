import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'پرداخت کارت', en: 'Card Payment' };
  const descriptions: Record<string, string> = { fa: 'پرداخت امن با کارت بانکی', en: 'Secure card payment' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/card`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/card`, languages: { fa: `${BASE_URL}/fa/market/checkout/card`, en: `${BASE_URL}/en/market/checkout/card` } },
  };
}

export default async function CardPaymentPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.card');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Payment Gateway" label={t('provenanceLabel')} verified={true} method="PCI-DSS" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['PCI-DSS Level 1', '3D Secure 2.0', 'Tokenization']}
          limits={['Redirect to gateway', 'Session timeout 10 min', 'Failed attempts locked']}
          next={['Save card for future', 'Enable 3DS', 'Add Apple/Google Pay']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-ink-soft mb-1">{t('cardNumber')}</label>
              <input type="text" placeholder="1234 5678 9012 3456" className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink text-lg focus:outline-none focus:ring-2 focus:ring-forest" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('expiryDate')}</label>
                <input type="text" placeholder="MM/YY" className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
              </div>
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('cvv')}</label>
                <input type="password" placeholder="123" className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
              </div>
            </div>
            <div>
              <label className="block text-sm text-ink-soft mb-1">{t('cardholderName')}</label>
              <input type="text" placeholder={t('cardholderPlaceholder')} className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
            </div>
            <Button variant="primary" className="w-full mt-4" disabled>{t('payNow')}</Button>
          </div>
        </Card>

        <div className="mt-6 flex gap-3">
          <Button variant="ghost" onClick={() => window.location.href = `/${locale}/market/checkout/ecowallet`}>
            Back
          </Button>
          <Button variant="primary" className="flex-1">{t('payNow')}</Button>
        </div>
      </section>
    </main>
  );
}