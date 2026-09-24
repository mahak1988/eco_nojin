import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface WalletFeature {
  id: string;
  name: string;
  description: string;
  status: 'live' | 'beta' | 'planned';
  apiEndpoint: string;
  source: string;
}

const MOCK_FEATURES: WalletFeature[] = [
  { id: 'wf1', name: 'Balance & Reserved', description: 'Real-time balance with escrow holds', status: 'live', apiEndpoint: 'GET /api/wallet/balance', source: 'ecowallet service' },
  { id: 'wf2', name: 'Transaction History', description: 'Filtered, paginated, exportable', status: 'live', apiEndpoint: 'GET /api/wallet/transactions', source: 'ecowallet service' },
  { id: 'wf3', name: 'Withdrawal Request', description: 'KYC-gated withdrawal to bank/mobile', status: 'live', apiEndpoint: 'POST /api/wallet/withdraw', source: 'ecowallet service' },
  { id: 'wf4', name: 'Escrow Center', description: 'View and manage active escrows', status: 'live', apiEndpoint: 'GET /api/wallet/escrows', source: 'escrow service' },
  { id: 'wf5', name: 'Microcredit Scoring', description: 'Farmer credit score for microloans', status: 'beta', apiEndpoint: 'GET /api/wallet/credit-score', source: 'finance service' },
  { id: 'wf6', name: 'Climate Insurance', description: 'Index-based payout triggers', status: 'planned', apiEndpoint: 'POST /api/wallet/insurance/claim', source: 'insurance service' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'نمایشگاه اکومین', en: 'EcoWallet Demo' };
  const descriptions: Record<string, string> = { fa: 'قابلیت‌های کیف پول دیجیتال', en: 'Digital wallet features showcase' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/ecowallet`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/ecowallet`, languages: { fa: `${BASE_URL}/fa/public/components/ecowallet`, en: `${BASE_URL}/en/public/components/ecowallet` } },
  };
}

export default async function EcoWalletPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.ecowallet');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Wallet Registry" label={t('provenanceLabel')} verified={true} method="Ledger-audited" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real ledger integration', 'Escrow-linked balances', 'Audit trail per transaction']}
          limits={['Sandbox balances only', 'KYC simulated', 'Bank integration mocked']}
          next={['Connect testnet ledger', 'Enable mobile money', 'Add DeFi bridge demo']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('features')}</h2>
        <div className="grid gap-4">
          {MOCK_FEATURES.map(f => (
            <Card key={f.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{f.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {f.status === 'live' ? 'bg-forest/10 text-forest' :
                       f.status === 'beta' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {f.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{f.description}</p>
                  <p className="text-xs text-ink-soft font-mono">{f.apiEndpoint}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={f.status === 'live' ? 'ok' : f.status === 'beta' ? 'warn' : 'down'} label={common(f.status)} />
                  <ProvenanceStamp source={f.source} verified={true} method="OpenAPI" label={f.status} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}