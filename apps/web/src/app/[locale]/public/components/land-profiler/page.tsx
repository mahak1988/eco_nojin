import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const PROFILES_PATH = '/api/v1/land/profiles';

type LandProfile = {
  id: string;
  name: string;
  location_lat: number | null;
  location_lon: number | null;
  area_ha: number | null;
  created_at: string | null;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-land-profiler');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/land-profiler`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/land-profiler'),
      languages: languageAlternates('/public/components/land-profiler'),
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

  const meta = await getTranslations('pageMeta.public-components-land-profiler');
  const statusPage = await getTranslations('statusPage');
  const title = meta('title');
  const description = meta('description');

  const profiles = await apiGet<LandProfile[]>(PROFILES_PATH);
  const rows = profiles.ok ? profiles.data : [];
  const state = toDataState(PROFILES_PATH, profiles, rows.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={PROFILES_PATH}
            label={title}
            verified={profiles.ok}
            method={PROFILES_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{statusPage('landProfileList')}</h2>
        <DataStateCard
          state={state}
          emptyTitle={statusPage('noLandProfiles')}
          emptyDescription={statusPage('emptyDbNote')}
        />
        {state.kind === 'ready' ? (
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
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
