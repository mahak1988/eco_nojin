import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../data-states';

const PLATFORM_STATS_PATH = '/api/v1/platform/stats';
const PILOT_STATS_PATH = '/api/v1/pilot/stats';
const MODELS_PATH = '/api/v1/models';

type PlatformStats = {
  db_backend: string;
  db_reachable: boolean;
  total_landscapes: number | null;
  total_projects: number | null;
  active_projects: number | null;
  cpp_available: boolean;
  error?: string;
};

type PilotStats = {
  applications: number;
  provinces: number;
  total_hectares: number;
  status: string;
  outcomes_status: string;
  generated_at: string;
};

type ModelsIndex = { count: number };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-home');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/home`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/home'),
      languages: languageAlternates('/public/home'),
    },
  };
}

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-home');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const title = meta('title');
  const description = meta('description');

  const [platform, pilot, models] = await Promise.all([
    apiGet<PlatformStats>(PLATFORM_STATS_PATH),
    apiGet<PilotStats>(PILOT_STATS_PATH),
    apiGet<ModelsIndex>(MODELS_PATH),
  ]);
  const platformState = toDataState(PLATFORM_STATS_PATH, platform, platform.ok ? 1 : 0);
  const pilotState = toDataState(PILOT_STATS_PATH, pilot, pilot.ok ? 1 : 0);
  const modelsState = toDataState(MODELS_PATH, models, models.ok ? models.data.count : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={PLATFORM_STATS_PATH}
            label={title}
            verified={platform.ok}
            method={PLATFORM_STATS_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
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

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{PILOT_STATS_PATH}</h2>
          <DataStateCard state={pilotState} />
          {pilotState.kind === 'ready' && pilot.ok ? (
            <div className="grid gap-4 sm:grid-cols-3">
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">{pilot.data.applications}</div>
                <p className="mt-1 text-sm text-ink-soft">{status('noData')}</p>
              </Card>
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">{pilot.data.provinces}</div>
                <p className="mt-1 text-sm text-ink-soft">{status('pilotProvince')}</p>
              </Card>
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">
                  {pilot.data.total_hectares}
                </div>
                <p className="mt-1 text-sm text-ink-soft">{pilot.data.status}</p>
              </Card>
            </div>
          ) : null}
          <SourceFooter state={pilotState} />
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{MODELS_PATH}</h2>
          <DataStateCard state={modelsState} />
          {modelsState.kind === 'ready' && models.ok ? (
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{models.data.count}</div>
              <p className="mt-1 text-sm text-ink-soft">{status('realData')}</p>
            </Card>
          ) : null}
          <SourceFooter state={modelsState} />
        </section>

        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href={`/${locale}/public/why`}
            className="inline-flex text-sm font-semibold text-[var(--color-forest)]"
          >
            {common('whatLabel')}
          </Link>
          <Link
            href={`/${locale}/public/channels`}
            className="inline-flex text-sm font-semibold text-[var(--color-forest)]"
          >
            {common('audienceLabel')}
          </Link>
          <Link
            href={`/${locale}/public/science/evidence-base`}
            className="inline-flex text-sm font-semibold text-[var(--color-forest)]"
          >
            {common('evidenceLabel')}
          </Link>
        </div>
      </div>
    </main>
  );
}
