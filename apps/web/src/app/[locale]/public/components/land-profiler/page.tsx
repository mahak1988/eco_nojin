import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const PROFILES_PATH = '/api/v1/land/profiles';

type LandProfile = {
  id: string;
  name: string;
  location_lat: number | null;
  location_lon: number | null;
  area_ha: number | null;
  created_at: string | null;
};

const TITLES: Record<string, string> = { fa: 'نمایشگاه پروفایلر زمین', en: 'Land Profiler Demo' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تحلیل زمین و سناریوهای مدیریتی',
  en: 'Land analysis and management scenarios',
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
      url: `${BASE_URL}/${locale}/public/components/land-profiler`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/land-profiler`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/land-profiler`,
        en: `${BASE_URL}/en/public/components/land-profiler`,
      },
    },
  };
}

const coordinate = (value: number | null) => (value === null ? '—' : String(value));

export default async function LandProfilerPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const statusPage = await getTranslations('statusPage');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const profiles = await apiGet<LandProfile[]>(PROFILES_PATH);
  const rows = profiles.ok ? profiles.data : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={PROFILES_PATH}
          label={title}
          verified={profiles.ok}
          method={PROFILES_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{statusPage('landProfileList')}</h2>
        {rows.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">
              {profiles.ok ? statusPage('noLandProfiles') : template('unavailableTitle')}
            </h3>
            <p className="mt-1 text-sm text-ink-soft">
              {profiles.ok ? statusPage('emptyDbNote') : template('unavailableDescription')}
            </p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {profiles.ok ? '' : ` · ${profiles.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="grid gap-4">
              {rows.map((profile) => (
                <Card key={profile.id} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">{profile.name}</h3>
                      <p className="mt-1 font-mono text-sm text-ink-soft">
                        {coordinate(profile.location_lat)} / {coordinate(profile.location_lon)} ·{' '}
                        {coordinate(profile.area_ha)} ha
                      </p>
                    </div>
                    <ProvenanceStamp
                      source={PROFILES_PATH}
                      verified={profiles.ok}
                      timestamp={profile.created_at ?? undefined}
                      method={profile.id}
                    />
                  </div>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {PROFILES_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
