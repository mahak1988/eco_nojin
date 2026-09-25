import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type LandProfile = { id: string; name: string; area_ha: number | null; created_at: string | null };

type PilotStats = {
  applications: number;
  provinces: number;
  total_hectares: number;
  status: string;
  outcomes_status: string;
  generated_at: string;
};

const TITLES: Record<string, string> = { fa: 'کشاورزان', en: 'Farmers' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تقاضای ثبت‌شده و پروفایل‌های زمین موجود در پایگاه داده',
  en: 'Registered applications and the land profiles present in the database',
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
      url: `${BASE_URL}/${locale}/public/audiences/farmers`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/audiences/farmers`,
      languages: {
        fa: `${BASE_URL}/fa/public/audiences/farmers`,
        en: `${BASE_URL}/en/public/audiences/farmers`,
      },
    },
  };
}

export default async function FarmersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');

  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const land = await apiGet<LandProfile[]>('/api/v1/land/profiles');
  const landState = toDataState('/api/v1/land/profiles', land, land.ok ? land.data.length : 0);
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
        <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/land/profiles'}</h2>
        <DataStateCard state={landState} />
        {landState.kind === 'ready' && land.ok ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {land.data.map((profile) => (
              <Card key={profile.id} density="compact">
                <h3 className="font-medium text-ink">{profile.name}</h3>
                <p className="num mt-1 text-sm text-ink-soft">
                  {profile.area_ha ?? status('unavailable')}
                </p>
                <div className="mt-2">
                  <ProvenanceStamp
                    source={'/api/v1/land/profiles'}
                    verified
                    timestamp={profile.created_at ?? undefined}
                    method={profile.id}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={landState} />
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
