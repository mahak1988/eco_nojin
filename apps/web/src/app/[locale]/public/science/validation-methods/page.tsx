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
  const meta = await getTranslations('pageMeta.public-science-validation-methods');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/validation-methods`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/science/validation-methods'),
      languages: languageAlternates('/public/science/validation-methods'),
    },
  };
}

export default async function ValidationMethodsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-science-validation-methods');
  const t = await getTranslations('statusLine');
  const title = meta('title');
  const description = meta('description');

  const report = await apiGet<ValidationReport>(VALIDATION_PATH);
  const checks = report.ok ? report.data.checks : [];
  const kinds = Array.from(new Set(checks.map((check) => check.kind)));
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

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{VALIDATION_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
          <>
            <div className="mb-4 flex flex-wrap gap-2">
              {kinds.map((kind) => (
                <span key={kind} className="px-2 py-1 rounded bg-forest/10 text-forest text-xs">
                  {kind}
                </span>
              ))}
            </div>
            <div className="grid gap-4">
              {checks.map((check) => (
                <Card key={check.id} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">{check.label}</h3>
                      <p className="mt-1 text-sm text-ink-soft">{check.source}</p>
                      {check.note ? (
                        <p className="mt-1 text-xs text-ink-soft">{check.note}</p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusDot
                        state={check.passed ? 'ok' : 'down'}
                        label={check.passed ? t('realData') : t('unavailable')}
                      />
                      <ProvenanceStamp
                        source={check.source}
                        verified={check.passed}
                        method={check.kind}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
