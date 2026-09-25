import { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type BlockchainInfo = {
  network: string;
  chain_id: number;
  contracts: Record<string, string>;
};

const TITLES: Record<string, string> = { fa: 'مأموریت', en: 'Mission' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'شبکه و قراردادهای دفترکل بازگشت‌شده از گیتوی',
  en: 'The ledger network and contracts returned by the gateway',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/goals/mission`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/goals/mission`,
      languages: {
        fa: `${BASE_URL}/fa/public/goals/mission`,
        en: `${BASE_URL}/en/public/goals/mission`,
      },
    },
  };
}

export default async function MissionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const ledger = await apiGet<BlockchainInfo>('/api/v1/blockchain/info');
  const ledgerState = toDataState('/api/v1/blockchain/info', ledger, ledger.ok ? 1 : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={'/api/v1/blockchain/info'}
          label={title}
          verified={ledger.ok}
          method={'/api/v1/blockchain/info'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/blockchain/info'}</h2>
          <DataStateCard state={ledgerState} />
          {ledgerState.kind === 'ready' && ledger.ok ? (
            <Card density="compact">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm text-ink">{ledger.data.network}</p>
                  <p className="num mt-1 font-mono text-xs text-ink-soft">{ledger.data.chain_id}</p>
                </div>
                <div className="grid gap-1">
                  {Object.entries(ledger.data.contracts).map(([name, address]) => (
                    <p key={name} className="num font-mono text-xs text-ink-soft">
                      {name} · {address}
                    </p>
                  ))}
                </div>
              </div>
              <div className="mt-3">
                <ProvenanceStamp
                  source={'/api/v1/blockchain/info'}
                  verified
                  method={'/api/v1/blockchain/info'}
                />
              </div>
            </Card>
          ) : null}
          <SourceFooter state={ledgerState} />
        </section>
      </div>
    </main>
  );
}
