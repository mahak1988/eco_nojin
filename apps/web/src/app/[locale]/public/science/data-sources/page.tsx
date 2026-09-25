import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const DATASETS_PATH = '/api/v1/science/datasets';

type Dataset = {
  id: string;
  name: string;
  domain: string;
  source: string;
  status: 'live' | 'offline';
  requires: string;
  license: string;
};

type DatasetCatalog = {
  count: number;
  live: number;
  datasets: Dataset[];
  note: string;
};

const TITLES: Record<string, string> = { fa: 'منابع داده', en: 'Data Sources' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'کاتالوگ منابع داده با وضعیت و مجوز',
  en: 'Data source catalog with status and licensing',
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
      url: `${BASE_URL}/${locale}/public/science/data-sources`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/data-sources`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/data-sources`,
        en: `${BASE_URL}/en/public/science/data-sources`,
      },
    },
  };
}

export default async function DataSourcesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const catalog = await apiGet<DatasetCatalog>(DATASETS_PATH);
  const data = catalog.ok ? catalog.data : null;
  const datasets = data ? data.datasets : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={DATASETS_PATH}
          label={title}
          verified={catalog.ok}
          method={DATASETS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{DATASETS_PATH}</h2>
        {datasets.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {catalog.ok ? '' : ` · ${catalog.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="grid gap-4">
              {datasets.map((dataset) => (
                <Card key={dataset.id} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-ink">{dataset.name}</h3>
                        <span className="text-xs px-2 py-1 rounded bg-forest/10 text-forest">
                          {dataset.domain}
                        </span>
                      </div>
                      <p className="text-sm text-ink-soft mt-1">{dataset.source}</p>
                      <p className="text-xs text-ink-soft mt-1">
                        {dataset.license} · {dataset.requires}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusDot
                        state={dataset.status === 'live' ? 'ok' : 'warn'}
                        label={dataset.status}
                      />
                      <ProvenanceStamp
                        source={dataset.source}
                        verified={dataset.status === 'live'}
                        method={dataset.id}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-ink-soft">
              <span>{t('realData')}</span>
              <span>
                {DATASETS_PATH} · {data?.count ?? 0} · {data?.live ?? 0}
              </span>
            </div>
            {data?.note ? <p className="mt-2 text-xs text-ink-soft">{data.note}</p> : null}
          </>
        )}
      </section>
    </main>
  );
}
