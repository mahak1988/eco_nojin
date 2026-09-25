import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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

const TITLES: Record<string, string> = { fa: 'نمایشگاه بازارگاه', en: 'Marketplace Demo' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'نمایش قابلیت‌های بازارگاه',
  en: 'Marketplace features demonstration',
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
      url: `${BASE_URL}/${locale}/public/components/marketplace`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/marketplace`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/marketplace`,
        en: `${BASE_URL}/en/public/components/marketplace`,
      },
    },
  };
}

export default async function MarketplacePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const market = await getTranslations('market');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [stats, producers] = await Promise.all([
    apiGet<MarketplaceStats>(STATS_PATH),
    apiGet<Producers>(PRODUCERS_PATH),
  ]);
  const rows = producers.ok ? producers.data.producers : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source={STATS_PATH} label={title} verified={stats.ok} method={STATS_PATH}>
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
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
        {rows.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">
              {producers.ok ? market('empty') : template('unavailableTitle')}
            </h3>
            <p className="mt-1 text-sm text-ink-soft">
              {producers.ok ? market('empty') : template('unavailableDescription')}
            </p>
          </Card>
        ) : (
          <>
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
            <p className="mt-6 text-xs text-ink-soft">
              {PRODUCERS_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
