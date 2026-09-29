import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const SUMMARY_PATH = '/api/v1/mrv/public/dashboard-summary';

type LatestSatellite = {
  site_id: string;
  index: string;
  value: number;
  data_source: string;
};

type MrvSummary = {
  total_observations: number;
  by_level: Record<string, number>;
  by_source: Record<string, number>;
  latest_satellite_per_site: LatestSatellite[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-mrv-dashboard');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/mrv-dashboard`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/mrv-dashboard'),
      languages: languageAlternates('/public/components/mrv-dashboard'),
    },
  };
}

export default async function MRVDashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-components-mrv-dashboard');
  const title = meta('title');
  const description = meta('description');

  const summary = await apiGet<MrvSummary>(SUMMARY_PATH);
  const data = summary.ok ? summary.data : null;
  const sites = data ? data.latest_satellite_per_site : [];
  const state = toDataState(SUMMARY_PATH, summary, data ? data.total_observations : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={SUMMARY_PATH}
            label={title}
            verified={summary.ok}
            method={SUMMARY_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SUMMARY_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' && data ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">{data.total_observations}</div>
                <p className="mt-1 text-sm text-ink-soft">{SUMMARY_PATH}</p>
                <ProvenanceStamp
                  source={SUMMARY_PATH}
                  verified={summary.ok}
                  method={SUMMARY_PATH}
                />
              </Card>
              {Object.entries(data.by_source).map(([source, count]) => (
                <Card key={source} density="compact">
                  <div className="num text-3xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">{source}</p>
                </Card>
              ))}
            </div>

            {sites.length > 0 ? (
              <div className="mt-8 grid gap-4">
                {sites.map((row) => (
                  <Card key={`${row.site_id}-${row.index}`} density="compact">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h3 className="font-mono text-sm font-medium text-ink">{row.site_id}</h3>
                        <p className="mt-1 text-sm text-ink-soft">
                          {row.index} · {row.value} · {row.data_source}
                        </p>
                      </div>
                      <ProvenanceStamp
                        source={SUMMARY_PATH}
                        verified={row.data_source !== 'simulated'}
                        method={row.data_source}
                      />
                    </div>
                  </Card>
                ))}
              </div>
            ) : null}
          </>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
