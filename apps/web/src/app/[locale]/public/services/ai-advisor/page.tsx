import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const AI_HEALTH_PATH = '/api/v1/ai/health';

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
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const health = await apiGet<AiHealth>(AI_HEALTH_PATH);

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={AI_HEALTH_PATH}
          label={services('title')}
          verified={health.ok}
          method={AI_HEALTH_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{AI_HEALTH_PATH}</h2>
        {health.ok ? (
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
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {health.error}
            </p>
          </Card>
        )}
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>

      <OwnerFooter />
    </main>
  );
}
