import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

type PilotStats = {
  applications: number;
  provinces: number;
  total_hectares: number;
  status: string;
  outcomes_status: string;
  generated_at: string;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-goals-impact');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/goals/impact`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/goals/impact'),
      languages: languageAlternates('/public/goals/impact'),
    },
  };
}

export default async function ImpactPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-goals-impact');
  const status = await getTranslations('statusLine');
  const title = meta('title');
  const description = meta('description');

  const pilot = await apiGet<PilotStats>('/api/v1/pilot/stats');
  const pilotState = toDataState('/api/v1/pilot/stats', pilot, pilot.ok ? 1 : 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={'/api/v1/pilot/stats'}
            label={title}
            verified={pilot.ok}
            method={'/api/v1/pilot/stats'}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
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
                <div className="num text-3xl font-semibold text-ink">
                  {pilot.data.total_hectares}
                </div>
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
      </div>
    </main>
  );
}
