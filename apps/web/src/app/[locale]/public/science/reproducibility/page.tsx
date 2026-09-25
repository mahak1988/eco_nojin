import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const SHARED_RUNS_PATH = '/api/v1/hub/shared';
const ZENODO_PATH = '/api/v1/science/zenodo/status';

type SharedRun = {
  id: string;
  model_id: string;
  title: string;
  outputs: Record<string, unknown> | null;
  created_at: string | null;
};

type SharedRuns = { ok: boolean; count: number; runs: SharedRun[] };

type ZenodoStatus = {
  configured: boolean;
  status: string;
  message: string;
  endpoint: string;
  sandbox?: boolean;
};

const TITLES: Record<string, string> = { fa: 'بازتولیدپذیری', en: 'Reproducibility' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'اجراهای عمومی ثبت‌شده و وضعیت واقعی صدور DOI',
  en: 'Registered shared runs and the real DOI issuance status',
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
      url: `${BASE_URL}/${locale}/public/science/reproducibility`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/reproducibility`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/reproducibility`,
        en: `${BASE_URL}/en/public/science/reproducibility`,
      },
    },
  };
}

export default async function ReproducibilityPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [runs, zenodo] = await Promise.all([
    apiGet<SharedRuns>(SHARED_RUNS_PATH),
    apiGet<ZenodoStatus>(ZENODO_PATH),
  ]);
  const sharedRuns = runs.ok ? runs.data.runs : [];
  const runsState = toDataState(SHARED_RUNS_PATH, runs, sharedRuns.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={SHARED_RUNS_PATH}
          label={title}
          verified={runs.ok}
          method={SHARED_RUNS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SHARED_RUNS_PATH}</h2>
        <DataStateCard state={runsState} />
        {runsState.kind === 'ready' && runs.ok ? (
          <div className="grid gap-4">
            {sharedRuns.map((run) => (
              <Card key={run.id} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">{run.title}</h3>
                    <p className="mt-1 font-mono text-xs text-ink-soft">{run.model_id}</p>
                    {run.created_at ? (
                      <p className="num mt-1 text-xs text-ink-soft">{run.created_at}</p>
                    ) : null}
                  </div>
                  <ProvenanceStamp
                    source={SHARED_RUNS_PATH}
                    verified={Boolean(run.created_at)}
                    timestamp={run.created_at ?? undefined}
                    method={run.id}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={runsState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{ZENODO_PATH}</h2>
        {zenodo.ok ? (
          <Card density="compact">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-ink">{zenodo.data.message}</p>
              <StatusDot
                state={zenodo.data.configured ? 'ok' : 'warn'}
                label={zenodo.data.status}
              />
            </div>
            <p className="mt-2 font-mono text-xs text-ink-soft">{zenodo.data.endpoint}</p>
            <div className="mt-3">
              <ProvenanceStamp source={ZENODO_PATH} verified method={ZENODO_PATH} />
            </div>
          </Card>
        ) : (
          <Card density="compact">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-medium text-ink">{status('unavailable')}</h3>
              <StatusDot state="down" label={status('unavailable')} />
            </div>
            <p className="mt-1 text-sm text-ink-soft">
              {ZENODO_PATH} · {zenodo.status} · {zenodo.error}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={ZENODO_PATH} verified={false} method={ZENODO_PATH} />
            </div>
          </Card>
        )}
      </section>
    </main>
  );
}
