import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const SUMMARY_PATH = '/api/v1/mrv/public/dashboard-summary';

type MrvSummary = {
  total_observations: number;
  by_level: Record<string, number>;
  by_source: Record<string, number>;
};

export const dynamic = 'force-dynamic';

export default async function MRVVerificationPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');

  const summary = await apiGet<MrvSummary>(SUMMARY_PATH);
  const data = summary.ok ? summary.data : null;
  const state = toDataState(SUMMARY_PATH, summary, data ? data.total_observations : 0);

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
          <ProvenanceStamp
            source={SUMMARY_PATH}
            label={services('title')}
            verified={summary.ok}
            method={SUMMARY_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
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
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              {Object.entries(data.by_level).map(([level, count]) => (
                <Card key={level} density="compact">
                  <div className="num text-2xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">level {level}</p>
                </Card>
              ))}
            </div>
          </>
        ) : null}
        <SourceFooter state={state} />
      </section>

      <OwnerFooter />
    </main>
  );
}
