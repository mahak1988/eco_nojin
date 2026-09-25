import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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

const TITLES: Record<string, string> = {
  fa: 'استخبارات ماهواره‌ای',
  en: 'Satellite Intelligence',
};
const DESCRIPTIONS: Record<string, string> = {
  fa: 'محصولات و اندپوینت‌های داده ماهواره',
  en: 'Satellite data products and endpoints',
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
      url: `${BASE_URL}/${locale}/public/services/satellite-intelligence`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/services/satellite-intelligence`,
      languages: {
        fa: `${BASE_URL}/fa/public/services/satellite-intelligence`,
        en: `${BASE_URL}/en/public/services/satellite-intelligence`,
      },
    },
  };
}

export default async function SatelliteIntelligencePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const [health, providers] = await Promise.all([
    apiGet<SatelliteHealth>(HEALTH_PATH),
    apiGet<Providers>(PROVIDERS_PATH),
  ]);
  const rows = providers.ok ? providers.data.providers : [];

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={HEALTH_PATH}
          label={services('title')}
          verified={health.ok}
          method={HEALTH_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {health.ok ? (
          <Card density="compact">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-sm font-medium text-ink">
                  {health.data.module} · {health.data.data_source}
                </h2>
                <p className="mt-1 text-xs text-ink-soft">
                  {health.data.supported_indices.join(', ')}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusDot
                  state={health.data.status === 'operational' ? 'ok' : 'warn'}
                  label={health.data.status}
                />
                <ProvenanceStamp source={HEALTH_PATH} verified={health.ok} method={HEALTH_PATH} />
              </div>
            </div>
          </Card>
        ) : (
          <Card density="compact">
            <h2 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {health.error}
            </p>
          </Card>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{PROVIDERS_PATH}</h2>
        {rows.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {providers.ok ? '' : ` · ${providers.error}`}
            </p>
          </Card>
        ) : (
          <>
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
            <p className="mt-6 text-xs text-ink-soft">
              {PROVIDERS_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>

      <OwnerFooter />
    </main>
  );
}
