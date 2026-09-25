import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { publicApi } from '@/lib/api/public';

export const dynamic = 'force-dynamic';

type ServiceStatus = {
  id: string;
  name: string;
  status: 'operational' | 'degraded' | 'maintenance' | 'offline';
  lastCheck: string;
  provenance: { source: string; verified?: boolean; timestamp?: string; method?: string };
};

export default async function ServicesOverviewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const servicesText = await getTranslations('services');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const overviewResult = await publicApi.services.overview();

  const services: ServiceStatus[] = overviewResult.ok ? overviewResult.data.services : [];
  const summary = overviewResult.ok
    ? overviewResult.data.summary
    : { total: 0, operational: 0, degraded: 0, offline: 0 };
  const provenance = overviewResult.ok
    ? overviewResult.data.provenance
    : { source: 'unknown', verified: false };

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={provenance.source}
          label={servicesText('title')}
          verified={provenance.verified}
          timestamp={provenance.timestamp}
          method={provenance.method}
        >
          <h1 className="display text-4xl font-bold text-ink">{servicesText('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{servicesText('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{servicesText('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{servicesText('audience')}</p>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('evidence').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('limits').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <ul className="mt-4 max-w-2xl list-inside list-disc space-y-1 text-sm text-ink-soft">
          {servicesText.raw('next').map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-sm font-semibold text-ink-soft">{servicesText('title')}</h2>
        {services.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {overviewResult.ok ? '' : ` · ${overviewResult.error}`}
            </p>
          </Card>
        ) : (
          <div className="mt-4 grid gap-4 sm:grid-cols-4">
            <Card density="compact">
              <div className="text-sm text-ink-soft">health</div>
              <div className="num mt-1 text-3xl font-semibold text-ink">{summary.total}</div>
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">operational</div>
              <div className="num mt-1 text-3xl font-semibold text-forest">
                {summary.operational}
              </div>
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">degraded</div>
              <div className="num mt-1 text-3xl font-semibold text-amber">{summary.degraded}</div>
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">offline</div>
              <div className="num mt-1 text-3xl font-semibold text-copper">{summary.offline}</div>
            </Card>
          </div>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-10">
        <h2 className="text-sm font-semibold text-ink-soft">{template('source')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <div key={service.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-ink">{service.name}</h3>
                  <p className="mt-1 font-mono text-xs text-ink-soft">
                    {service.provenance.method ?? service.provenance.source}
                  </p>
                </div>
                <ProvenanceStamp
                  source={service.provenance.source}
                  verified={service.provenance.verified}
                  timestamp={service.provenance.timestamp}
                  method={service.provenance.method}
                />
              </div>
              <div className="mt-3">
                <StatusDot
                  state={
                    service.status === 'operational'
                      ? 'ok'
                      : service.status === 'degraded'
                        ? 'warn'
                        : 'down'
                  }
                  label={service.status}
                />
              </div>
              <p className="num mt-3 font-mono text-xs text-ink-soft">
                {new Date(service.lastCheck).toLocaleString(locale)}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>

      <OwnerFooter />
    </main>
  );
}
