import { getTranslations, setRequestLocale } from 'next-intl/server';
import { publicApi } from '@/lib/api/public';
import { Link } from '@/i18n/navigation';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { SiteNav } from '@/components/SiteNav';
import { OwnerFooter } from '@/components/OwnerFooter';

interface ServiceStatus {
  id: string;
  name: string;
  status: 'operational' | 'degraded' | 'maintenance' | 'offline';
  latencyMs?: number;
  lastCheck: string;
  provenance: {
    source: string;
    verified?: boolean;
    timestamp?: string;
    method?: string;
  };
}

export const dynamic = 'force-dynamic';

export default async function ServicesOverviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.services');

  const overviewResult = await publicApi.services.overview();

  const services: ServiceStatus[] = overviewResult.ok ? overviewResult.data.services : [];
  const summary = overviewResult.ok ? overviewResult.data.summary : { total: 0, operational: 0, degraded: 0, offline: 0 };
  const provenance = overviewResult.ok ? overviewResult.data.provenance : { source: 'unknown', verified: false };

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <FivePart
        title={t('title')}
        lead={t('lead')}
        what={t('what')}
        audience={t('audience')}
        evidence={t.raw('evidence') as string[]}
        limits={t.raw('limits') as string[]}
        next={t.raw('next') as string[]}
      />

      <section className="mx-auto max-w-5xl px-6 py-6">
        <h2 className="text-sm font-semibold text-ink-soft">{t('summary.title')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-4">
          <Card density="compact">
            <div className="text-sm text-ink-soft">{t('summary.total')}</div>
            <div className="num mt-1 text-3xl font-semibold text-ink">{summary.total}</div>
            <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
          </Card>
          <Card density="compact">
            <div className="text-sm text-ink-soft">{t('summary.operational')}</div>
            <div className="num mt-1 text-3xl font-semibold text-forest">{summary.operational}</div>
            <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
          </Card>
          <Card density="compact">
            <div className="text-sm text-ink-soft">{t('summary.degraded')}</div>
            <div className="num mt-1 text-3xl font-semibold text-amber">{summary.degraded}</div>
            <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
          </Card>
          <Card density="compact">
            <div className="text-sm text-ink-soft">{t('summary.offline')}</div>
            <div className="num mt-1 text-3xl font-semibold text-copper">{summary.offline}</div>
            <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
          </Card>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6">
        <h2 className="text-sm font-semibold text-ink-soft">{t('detail.title')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('detail.description')}</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <Link key={service.id} href={`/public/services/${service.id}`} className="card p-4 hover:border-water transition-colors">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-ink">{service.name}</h3>
                  <p className="mt-1 text-sm text-ink-soft">{service.provenance.source}</p>
                </div>
                <ProvenanceStamp source={service.provenance.source} verified={service.provenance.verified} timestamp={service.provenance.timestamp} method={service.provenance.method} />
              </div>
              <div className="mt-3 flex items-center gap-3">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                  service.status === 'operational' ? 'bg-forest/10 text-forest' :
                  service.status === 'degraded' ? 'bg-amber/10 text-amber' :
                  service.status === 'maintenance' ? 'bg-blue/10 text-blue' : 'bg-copper/10 text-copper'
                }`}>
                  {t(`status.${service.status}`)}
                </span>
                {service.latencyMs !== undefined && (
                  <span className="text-xs text-ink-soft">
                    {t('latency')}: <span className="num font-mono">{service.latencyMs} ms</span>
                  </span>
                )}
              </div>
              <p className="mt-3 text-xs text-ink-soft">
                {t('lastCheck')}: <span className="num font-mono">{new Date(service.lastCheck).toLocaleString(locale)}</span>
              </p>
              <p className="mt-3 text-xs text-water hover:underline">{t('detail.learnMore')}</p>
            </Link>
          ))}
        </div>
      </section>

      <p className="mx-auto max-w-5xl px-6 mt-10 text-xs text-ink-soft">{t('provenance.note')}</p>
      <OwnerFooter />
    </main>
  );
}