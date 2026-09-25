import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const LAND_HEALTH_PATH = '/api/v1/land/health';
const PROFILES_PATH = '/api/v1/land/profiles';

type LandHealth = {
  status: string;
  service: string;
  profiles_count: number;
};

type LandProfile = {
  id: string;
  name: string;
  area_ha: number | null;
  created_at: string | null;
};

export const dynamic = 'force-dynamic';

const area = (value: number | null) => (value === null ? '—' : String(value));

export default async function LandIntelligencePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');
  const statusPage = await getTranslations('statusPage');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const [health, profiles] = await Promise.all([
    apiGet<LandHealth>(LAND_HEALTH_PATH),
    apiGet<LandProfile[]>(PROFILES_PATH),
  ]);
  const rows = profiles.ok ? profiles.data : [];

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={LAND_HEALTH_PATH}
          label={services('title')}
          verified={health.ok}
          method={LAND_HEALTH_PATH}
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
                  {health.data.service} · {health.data.profiles_count}
                </h2>
                <p className="mt-1 text-xs text-ink-soft">{statusPage('landProfileList')}</p>
              </div>
              <div className="flex items-center gap-3">
                <StatusDot
                  state={health.data.status === 'healthy' ? 'ok' : 'warn'}
                  label={health.data.status}
                />
                <ProvenanceStamp
                  source={LAND_HEALTH_PATH}
                  verified={health.ok}
                  method={LAND_HEALTH_PATH}
                />
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
        <h2 className="text-xl font-semibold text-ink mb-4">{PROFILES_PATH}</h2>
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
                        {area(profile.area_ha)} ha
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

      <OwnerFooter />
    </main>
  );
}
