import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

type PlatformStats = {
  db_backend: string;
  db_reachable: boolean;
  total_landscapes: number | null;
  total_projects: number | null;
  active_projects: number | null;
};

type PilotStats = {
  applications: number;
  provinces: number;
  total_hectares: number;
  status: string;
  outcomes_status: string;
  generated_at: string;
};

const TITLES: Record<string, string> = { fa: 'سرمایه‌گذاران', en: 'Investors' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تقاضای ثبت‌شده و شمار واقعی پروژه‌ها؛ بدون ادعای بازده',
  en: 'Registered applications and real project counters; no return is claimed',
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
      url: `${BASE_URL}/${locale}/public/audiences/investors`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/audiences/investors`,
      languages: {
        fa: `${BASE_URL}/fa/public/audiences/investors`,
        en: `${BASE_URL}/en/public/audiences/investors`,
      },
    },
  };
}

export default async function InvestorsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const common = await getTranslations('common');

  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const platform = await apiGet<PlatformStats>('/api/v1/platform/stats');
  const platformState = toDataState('/api/v1/platform/stats', platform, platform.ok ? 1 : 0);
  const pilot = await apiGet<PilotStats>('/api/v1/pilot/stats');
  const pilotState = toDataState('/api/v1/pilot/stats', pilot, pilot.ok ? 1 : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={'/api/v1/pilot/stats'}
          label={title}
          verified={pilot.ok}
          method={'/api/v1/pilot/stats'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/platform/stats'}</h2>
        <DataStateCard state={platformState} />
        {platformState.kind === 'ready' && platform.ok ? (
          <div className="grid gap-4 sm:grid-cols-4">
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
            <Card density="compact">
              <p className="text-sm text-ink">{platform.data.db_backend}</p>
              <p className="num mt-1 text-xs text-ink-soft">
                {platform.data.db_reachable ? common('live') : status('unavailable')}
              </p>
            </Card>
          </div>
        ) : null}
        <SourceFooter state={platformState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/pilot/stats'}</h2>
        <DataStateCard state={pilotState} />
        {pilotState.kind === 'ready' && pilot.ok ? (
          <div className="grid gap-4 sm:grid-cols-4">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{pilot.data.applications}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('noData')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{pilot.data.provinces}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('pilotProvince')}</p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{pilot.data.total_hectares}</div>
              <p className="mt-1 text-sm text-ink-soft">{pilot.data.status}</p>
            </Card>
            <Card density="compact">
              <p className="text-sm text-ink">{pilot.data.outcomes_status}</p>
              <p className="num mt-1 text-xs text-ink-soft">{pilot.data.generated_at}</p>
            </Card>
          </div>
        ) : null}
        <SourceFooter state={pilotState} />
      </section>
    </main>
  );
}
