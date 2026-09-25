import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const VALIDATION_PATH = '/api/v1/hydroma/validation';
const PLATFORM_STATS_PATH = '/api/v1/platform/stats';

type ValidationReport = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  checks: { id: string; label: string; source: string; passed: boolean; note: string }[];
};

type PlatformStats = {
  db_backend: string;
  db_reachable: boolean;
  total_landscapes: number | null;
  total_projects: number | null;
  active_projects: number | null;
};

const TITLES: Record<string, string> = { fa: 'چرا این سامانه', en: 'Why this platform' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مسئله، راه‌حل و شواهد قابل بررسی',
  en: 'The problem, the solution, and the checkable evidence',
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
      url: `${BASE_URL}/${locale}/public/why`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/why`,
      languages: {
        fa: `${BASE_URL}/fa/public/why`,
        en: `${BASE_URL}/en/public/why`,
      },
    },
  };
}

export default async function WhyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('why');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const title = TITLES[locale] ?? TITLES.en;

  // The claim behind the "solution" column is only stated when the executed
  // formula-check suite and the database counters actually back it.
  const [report, platform] = await Promise.all([
    apiGet<ValidationReport>(VALIDATION_PATH),
    apiGet<PlatformStats>(PLATFORM_STATS_PATH),
  ]);
  const checks = report.ok ? report.data.checks : [];
  const validationState = toDataState(VALIDATION_PATH, report, checks.length);
  const platformState = toDataState(PLATFORM_STATS_PATH, platform, platform.ok ? 1 : 0);

  const problems = t.raw('problemRows') as { problem: string; solution: string }[];

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
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={t.raw('evidenceItems') as string[]}
          limits={t.raw('limitsItems') as string[]}
          next={t.raw('nextItems') as string[]}
          evidenceLabel={common('evidence')}
          limitsLabel={common('limits')}
          nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{VALIDATION_PATH}</h2>
        <DataStateCard state={validationState} />
        {validationState.kind === 'ready' && report.ok ? (
          <div className="grid gap-4 sm:grid-cols-4">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{report.data.total}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('realData')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-forest">{report.data.passed}</div>
              <p className="mt-1 text-sm text-ink-soft">{common('live')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-copper">{report.data.failed}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('unavailable')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{report.data.pass_rate}</div>
              <p className="mt-1 text-sm text-ink-soft">{t('solution')}</p>
            </Card>
          </div>
        ) : null}
        <SourceFooter state={validationState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{PLATFORM_STATS_PATH}</h2>
        <DataStateCard state={platformState} />
        {platformState.kind === 'ready' && platform.ok ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {platform.data.total_landscapes ?? status('unavailable')}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{status('landProfiles')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {platform.data.total_projects ?? status('unavailable')}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{status('carbonProjects')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {platform.data.active_projects ?? status('unavailable')}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{status('carbonProjects')}</p>
            </Card>
          </div>
        ) : null}
        <SourceFooter state={platformState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('problemSolutionTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-start py-2 px-3 font-medium text-ink-soft">{t('problem')}</th>
                <th className="text-start py-2 px-3 font-medium text-ink-soft">{t('solution')}</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p) => (
                <tr key={p.problem} className="border-b border-line/50">
                  <td className="py-2 px-3 text-ink-soft">{p.problem}</td>
                  <td className="py-2 px-3 text-ink">{p.solution}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
          <ProvenanceStamp
            source={VALIDATION_PATH}
            verified={report.ok}
            method={VALIDATION_PATH}
            label={t('provenanceLabel')}
          />
        </div>
      </section>
    </main>
  );
}
