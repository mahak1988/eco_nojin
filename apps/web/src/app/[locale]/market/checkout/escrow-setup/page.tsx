import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'تنظیم اسکرو', en: 'Escrow Setup' };
  const descriptions: Record<string, string> = { fa: 'تنظیم امانیت و انتخاب روش پرداخت', en: 'Configure escrow and choose payment method' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/escrow-setup`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/escrow-setup`, languages: { fa: `${BASE_URL}/fa/market/checkout/escrow-setup`, en: `${BASE_URL}/en/market/checkout/escrow-setup` } },
  };
}

export default async function EscrowSetupPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.escrowSetup');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Escrow Service" label={t('provenanceLabel')} verified={true} method="Smart contract" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['5-party PQ signatures', 'Funds locked on-chain', 'Auto-release on delivery']}
          limits={['Gas fees apply', 'Dispute window 14 days', 'Cancellation fees may apply']}
          next={['Accept contract', 'Generate transaction key', 'Fund escrow']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="compact">
          <h2 className="font-semibold text-ink mb-4">{t('paymentMethod')}</h2>
          <div className="space-y-3">
            <label className="flex items-center gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="radio" name="payment" className="w-4 h-4 text-forest focus:ring-forest" defaultChecked />
              <div className="flex-1">
                <h3 className="font-medium text-ink">{t('ecowallet')}</h3>
                <p className="text-sm text-ink-soft">{t('ecowalletDesc')}</p>
              </div>
              <StatusDot state="ok" label={common('recommended')} />
            </label>
            <label className="flex items-center gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="radio" name="payment" className="w-4 h-4 text-forest focus:ring-forest" />
              <div className="flex-1">
                <h3 className="font-medium text-ink">{t('card')}</h3>
                <p className="text-sm text-ink-soft">{t('cardDesc')}</p>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="radio" name="payment" className="w-4 h-4 text-forest focus:ring-forest" />
              <div className="flex-1">
                <h3 className="font-medium text-ink">{t('bankTransfer')}</h3>
                <p className="text-sm text-ink-soft">{t('bankTransferDesc')}</p>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="radio" name="payment" className="w-4 h-4 text-forest focus:ring-forest" />
              <div className="flex-1">
                <h3 className="font-medium text-ink">{t('installments')}</h3>
                <p className="text-sm text-ink-soft">{t('installmentsDesc')}</p>
              </div>
            </label>
          </div>
        </Card>

        <Card density="compact" className="mt-6">
          <h2 className="font-semibold text-ink mb-4">{t('contractAcceptance')}</h2>
          <div className="space-y-3">
            <label className="flex items-start gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="checkbox" className="mt-1 w-4 h-4 text-forest focus:ring-forest" />
              <div className="text-sm text-ink-soft">
                <span className="font-medium text-ink">{t('contractTerms')}</span>
                <a href={`/${locale}/market/checkout/contract`} className="text-forest underline ml-1">{t('viewContract')}</a>
              </div>
            </label>
            <label className="flex items-start gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="checkbox" className="mt-1 w-4 h-4 text-forest focus:ring-forest" />
              <div className="text-sm text-ink-soft">
                <span className="font-medium text-ink">{t('escrowTerms')}</span>
                <a href={`/${locale}/market/checkout/escrow-status`} className="text-forest underline ml-1">{t('viewEscrowTerms')}</a>
              </div>
            </label>
            <label className="flex items-start gap-3 p-3 border border-line rounded cursor-pointer hover:bg-forest/5">
              <input type="checkbox" className="mt-1 w-4 h-4 text-forest focus:ring-forest" />
              <div className="text-sm text-ink-soft">
                <span className="font-medium text-ink">{t('disputeResolution')}</span>
                <a href={`/${locale}/market/checkout/escrow-dispute`} className="text-forest underline ml-1">{t('viewDisputeTerms')}</a>
              </div>
            </label>
          </div>
        </Card>

        <Button variant="primary" className="w-full mt-6" onClick={() => window.location.href = `/${locale}/market/checkout/transaction-key`}>
          {t('generateTransactionKey')}
        </Button>
      </section>
    </main>
  );
}