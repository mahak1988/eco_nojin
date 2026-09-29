import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const VALIDATION_PATH = '/api/v1/hydroma/validation';

type ValidationCheck = {
  id: string;
  label: string;
  kind: string;
  source: string;
  expected: number | string;
  actual: number | string;
  tolerance: number;
  unit: string;
  passed: boolean;
  note: string;
};

type ValidationReport = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  checks: ValidationCheck[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-science-benchmarks');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/benchmarks`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/science/benchmarks'),
      languages: languageAlternates('/public/science/benchmarks'),
    },
  };
}

export default async function BenchmarksPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-science-benchmarks');
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = meta('title');
  const description = meta('description');

  // The independent formula-verification suite is the only measured comparison the
  // gateway publishes: every row is an executed check against a cited reference.
  const report = await apiGet<ValidationReport>(VALIDATION_PATH);
  const checks = report.ok ? report.data.checks : [];
  const state = toDataState(VALIDATION_PATH, report, checks.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={VALIDATION_PATH}
            label={title}
            verified={report.ok}
            method={VALIDATION_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      {state.kind === 'ready' && report.ok ? (
        <section className="mx-auto max-w-5xl px-6 pb-6">
          <div className="grid gap-4 sm:grid-cols-4">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{report.data.total}</div>
              <p className="mt-1 text-sm text-ink-soft">{template('source')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-forest">{report.data.passed}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('realData')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-copper">{report.data.failed}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('unavailable')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{report.data.pass_rate}</div>
              <p className="mt-1 text-sm text-ink-soft">{template('status')}</p>
            </Card>
          </div>
        </section>
      ) : null}

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{VALIDATION_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' && report.ok ? (
          <div className="grid gap-4">
            {checks.map((check) => (
              <Card key={check.id} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">{check.label}</h3>
                    <p className="mt-1 text-sm text-ink-soft">{check.source}</p>
                    <p className="num mt-1 text-xs text-ink-soft">
                      {check.expected} / {check.actual} · {check.tolerance} {check.unit}
                    </p>
                    {check.note ? <p className="mt-1 text-xs text-ink-soft">{check.note}</p> : null}
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusDot state={check.passed ? 'ok' : 'down'} label={check.kind} />
                    <ProvenanceStamp
                      source={check.source}
                      verified={check.passed}
                      method={check.id}
                    />
                  </div>
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
