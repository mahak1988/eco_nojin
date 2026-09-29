import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const AI_HEALTH_PATH = '/api/v1/ai/health';
const AI_PROVIDERS_PATH = '/api/v1/ai/analysis/providers';

type AiProviders = { providers: string[] };

type AiHealth = {
  status: string;
  engine_type: string;
  providers_configured?: boolean;
  error?: string;
};

export const dynamic = 'force-dynamic';

export default async function AIAdvisorPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');

  const [health, providers] = await Promise.all([
    apiGet<AiHealth>(AI_HEALTH_PATH),
    apiGet<AiProviders>(AI_PROVIDERS_PATH),
  ]);
  const healthState = toDataState(AI_HEALTH_PATH, health, health.ok ? 1 : 0);
  const providerRows = providers.ok ? providers.data.providers : [];
  const providersState = toDataState(AI_PROVIDERS_PATH, providers, providerRows.length);

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
          <ProvenanceStamp
            source={AI_HEALTH_PATH}
            label={services('title')}
            verified={health.ok}
            method={AI_HEALTH_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{AI_HEALTH_PATH}</h2>
        {healthState.kind === 'ready' && health.ok ? (
          <Card density="compact">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="font-medium text-ink">{health.data.engine_type}</h3>
                {health.data.error ? (
                  <p className="mt-1 text-sm text-ink-soft">{health.data.error}</p>
                ) : null}
              </div>
              <div className="flex items-center gap-3">
                <StatusDot
                  state={health.data.status === 'operational' ? 'ok' : 'warn'}
                  label={health.data.status}
                />
                <ProvenanceStamp
                  source={AI_HEALTH_PATH}
                  verified={health.ok}
                  method={AI_HEALTH_PATH}
                />
              </div>
            </div>
          </Card>
        ) : (
          <DataStateCard state={healthState} />
        )}
        <SourceFooter state={healthState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{AI_PROVIDERS_PATH}</h2>
        <DataStateCard state={providersState} />
        {providersState.kind === 'ready' && providers.ok ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {providerRows.map((provider) => (
              <Card key={provider} density="compact">
                <h3 className="font-medium text-ink">{provider}</h3>
                <div className="mt-2">
                  <ProvenanceStamp source={AI_PROVIDERS_PATH} verified method={provider} />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={providersState} />
      </section>

      <OwnerFooter />
    </main>
  );
}
