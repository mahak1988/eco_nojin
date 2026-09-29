import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const STATS_PATH = '/api/v1/marketplace/stats';
const PRODUCERS_PATH = '/api/v1/marketplace/producers';

type MarketplaceStats = {
  total_products: number;
  total_producers: number;
  organic_products: number;
  orders: unknown;
};

type Producer = {
  id: string;
  name: string;
  location: string;
  producer_type: string;
  certifications: string[];
};

type Producers = {
  producers: Producer[];
  count: number;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-marketplace');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/marketplace`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/marketplace'),
      languages: languageAlternates('/public/components/marketplace'),
    },
  };
}

export default async function MarketplacePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-components-marketplace');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const market = await getTranslations('market');
  const title = meta('title');
  const description = meta('description');

  const [stats, producers] = await Promise.all([
    apiGet<MarketplaceStats>(STATS_PATH),
    apiGet<Producers>(PRODUCERS_PATH),
  ]);
  const rows = producers.ok ? producers.data.producers : [];
  const state = toDataState(PRODUCERS_PATH, producers, rows.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={STATS_PATH}
            label={title}
            verified={stats.ok}
            method={STATS_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {stats.ok ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{stats.data.total_products}</div>
              <p className="mt-1 text-sm text-ink-soft">{market('products')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {stats.data.total_producers}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{market('producers')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {stats.data.organic_products}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{market('organic')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
          </div>
        ) : (
          <Card density="compact">
            <h2 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {stats.error}
            </p>
          </Card>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{PRODUCERS_PATH}</h2>
        <DataStateCard
          state={state}
          emptyTitle={market('empty')}
          emptyDescription={market('empty')}
        />
        {state.kind === 'ready' ? (
          <div className="grid gap-4">
            {rows.map((producer) => (
              <Card key={producer.id} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">{producer.name}</h3>
                    <p className="mt-1 text-sm text-ink-soft">
                      {producer.location} · {producer.producer_type}
                    </p>
                    {producer.certifications.length > 0 ? (
                      <div className="mt-2 flex flex-wrap gap-1 text-xs">
                        {producer.certifications.map((certification) => (
                          <span
                            key={certification}
                            className="px-1.5 py-0.5 rounded bg-forest/10 text-forest"
                          >
                            {certification}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <ProvenanceStamp
                    source={PRODUCERS_PATH}
                    verified={producers.ok}
                    method={producer.producer_type}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
