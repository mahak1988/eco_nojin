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

const HEALTH_PATH = '/api/v1/satellite/health';
const PROVIDERS_PATH = '/api/v1/satellite/providers';

type SatelliteHealth = {
  status: string;
  module: string;
  supported_indices: string[];
  providers: string[];
  data_source: string;
};

type Providers = { providers: string[] };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-satellite-view');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/satellite-view`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/satellite-view'),
      languages: languageAlternates('/public/components/satellite-view'),
    },
  };
}

export default async function SatelliteViewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-components-satellite-view');
  const title = meta('title');
  const description = meta('description');

  const [health, providers] = await Promise.all([
    apiGet<SatelliteHealth>(HEALTH_PATH),
    apiGet<Providers>(PROVIDERS_PATH),
  ]);
  const rows = providers.ok ? providers.data.providers : [];
  const healthState = toDataState(HEALTH_PATH, health, health.ok ? 1 : 0);
  const providersState = toDataState(PROVIDERS_PATH, providers, rows.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={HEALTH_PATH}
            label={title}
            verified={health.ok}
            method={HEALTH_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {healthState.kind === 'ready' && health.ok ? (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">
                {health.data.module} · {health.data.data_source}
              </p>
              <StatusDot
                state={health.data.status === 'operational' ? 'ok' : 'warn'}
                label={health.data.status}
              />
            </div>
            <p className="mt-1 text-xs text-ink-soft">{health.data.supported_indices.join(', ')}</p>
            <div className="mt-2">
              <ProvenanceStamp source={HEALTH_PATH} verified={health.ok} method={HEALTH_PATH} />
            </div>
          </Card>
        ) : (
          <DataStateCard state={healthState} />
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{PROVIDERS_PATH}</h2>
        <DataStateCard state={providersState} />
        {providersState.kind === 'ready' && providers.ok ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {rows.map((provider) => (
              <Card key={provider} density="compact">
                <h3 className="font-medium text-ink">{provider}</h3>
                <div className="mt-2">
                  <ProvenanceStamp
                    source={PROVIDERS_PATH}
                    verified={providers.ok}
                    method={PROVIDERS_PATH}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={providersState} />
      </section>
    </main>
  );
}
