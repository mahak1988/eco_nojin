import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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

const TITLES: Record<string, string> = { fa: 'روش‌های اعتبارسنجی', en: 'Validation Methods' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'روش‌های اعتبارسنجی مدل‌های علمی',
  en: 'Scientific model validation methodologies',
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
      url: `${BASE_URL}/${locale}/public/science/validation-methods`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/validation-methods`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/validation-methods`,
        en: `${BASE_URL}/en/public/science/validation-methods`,
      },
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
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const report = await apiGet<ValidationReport>(VALIDATION_PATH);
  const checks = report.ok ? report.data.checks : [];
  const kinds = Array.from(new Set(checks.map((check) => check.kind)));

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={VALIDATION_PATH}
          label={title}
          verified={report.ok}
          method={VALIDATION_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        {checks.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {report.ok ? '' : ` · ${report.error}`}
            </p>
          </Card>
        ) : (
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
                        label={check.passed ? 'pass' : 'fail'}
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
            <p className="mt-6 text-xs text-ink-soft">
              {VALIDATION_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
