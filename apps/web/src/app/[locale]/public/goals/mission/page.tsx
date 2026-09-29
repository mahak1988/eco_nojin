import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

type BlockchainInfo = {
  network: string;
  chain_id: number;
  contracts: Record<string, string>;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-goals-mission');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/goals/mission`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/goals/mission'),
      languages: languageAlternates('/public/goals/mission'),
    },
  };
}

export default async function MissionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-goals-mission');
  const title = meta('title');
  const description = meta('description');

  const ledger = await apiGet<BlockchainInfo>('/api/v1/blockchain/info');
  const ledgerState = toDataState('/api/v1/blockchain/info', ledger, ledger.ok ? 1 : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={'/api/v1/blockchain/info'}
            label={title}
            verified={ledger.ok}
            method={'/api/v1/blockchain/info'}
          />
        </div>
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
