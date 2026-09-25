import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const DATASETS_PATH = '/api/v1/science/datasets';

type DatasetCatalog = {
  count: number;
  live: number;
};

const TITLES: Record<string, string> = { fa: 'معیارهای مقایسه', en: 'Benchmarks' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'بندمارک‌های استاندارد برای ارزیابی مدل‌ها',
  en: 'Standard benchmarks for model evaluation',
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
      url: `${BASE_URL}/${locale}/public/science/benchmarks`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/benchmarks`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/benchmarks`,
        en: `${BASE_URL}/en/public/science/benchmarks`,
      },
    },
  };
}

export default async function BenchmarksPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // No benchmark results are published by the API gateway; only the honest
  // dataset availability report exists, so the results table stays empty.
  const datasets = await apiGet<DatasetCatalog>(DATASETS_PATH);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={DATASETS_PATH}
          label={title}
          verified={datasets.ok}
          method={template('method')}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
          <p className="mt-3 text-xs text-ink-soft">
            {template('method')} · {t('unavailable')}
          </p>
        </Card>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>
    </main>
  );
}
