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
  const titles: Record<string, string> = { fa: 'پرداخت با اکومین', en: 'EcoWallet Payment' };
  const descriptions: Record<string, string> = { fa: 'پرداخت از موجودی کیف پول', en: 'Pay from wallet balance' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/ecowallet`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/ecowallet`, languages: { fa: `${BASE_URL}/fa/market/checkout/ecowallet`, en: `${BASE_URL}/en/market/checkout/ecowallet` } },
  };
}

export default async function EcoWalletPaymentPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.ecowallet');
  const common = await getTranslations('common');

  const balance = 5000000;
  const total = 12500000;
  const formatPrice = (p: number) => new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Wallet Service" label={t('provenanceLabel')} verified={true} method="Ledger-verified" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real-time balance', 'Instant settlement', 'Escrow-linked']}
          limits={['Insufficient balance', 'KYC required for >50M', 'Daily limit 100M']}
          next={['Add funds', 'Enable auto-topup', 'Link bank account']}
          evidenceLabel="Evidence" limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="compact">
          <h2 className="font-semibold text-ink mb-4">{t('walletBalance')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between"><span className="text-ink-soft">{t('availableBalance')}</span><span className="font-bold text-forest text-xl">{new Intl.NumberFormat('fa-IR').format(balance)} ریال</span></div>
            <div className="flex justify-between"><span className="text-ink-soft">{t('orderTotal')}</span><span className="font-bold text-ink">{new Intl.NumberFormat('fa-IR').format(12500000)} ریال</span></div>
            <div className="flex justify-between border-t border-line pt-3"><span className="text-ink-soft">{t('remainingAfterPayment')}</span><span className="font-bold text-forest">{new Intl.NumberFormat('fa-IR').format(balance - 12500000)} ریال</span></div>
          </div>
        </Card>

        <div className="mt-6 flex gap-3">
          <Button variant="ghost" onClick={() => window.location.href = `/${locale}/market/checkout/transaction-key`}>
            Back
          </Button>
          <Button variant="primary" className="flex-1" disabled={balance < 12500000}>
            {balance < 12500000 ? t('insufficientFunds') : t('confirmPayment')}
          </Button>
        </div>
      </section>
    </main>
  );
}