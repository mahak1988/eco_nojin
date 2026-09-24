import { getTranslations, setRequestLocale } from 'next-intl/server';
import { publicApi } from '@/lib/api/public';
import { Link } from '@/i18n/navigation';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { SiteNav } from '@/components/SiteNav';
import { OwnerFooter } from '@/components/OwnerFooter';

interface ServiceDetail {
  id: string;
  name: string;
  description?: string;
  status: 'operational' | 'degraded' | 'maintenance' | 'offline';
  latencyMs?: number;
  lastCheck: string;
  capabilities?: string[];
  endpoints?: string[];
  provenance: {
    source: string;
    verified?: boolean;
    timestamp?: string;
    method?: string;
  };
}

export const dynamic = 'force-dynamic';

export default async function MarketplaceAccessPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.services.marketplaceAccess');

  const statusResult = await publicApi.services.status('marketplace-access');

  const service: ServiceDetail | null = statusResult.ok ? statusResult.data : null;
  const provenance = service?.provenance ?? { source: 'unknown', verified: false };

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

      {service && (
        <section className="mx-auto max-w-5xl px-6 py-6">
          <h2 className="text-sm font-semibold text-ink-soft">{t('status.title')}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-4">
            <Card density="compact">
              <div className="text-sm text-ink-soft">{t('status.label')}</div>
              <div className="num mt-1 text-3xl font-semibold text-ink">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                  service.status === 'operational' ? 'bg-forest/10 text-forest' :
                  service.status === 'degraded' ? 'bg-amber/10 text-amber' :
                  service.status === 'maintenance' ? 'bg-blue/10 text-blue' : 'bg-copper/10 text-copper'
                }`}>
                  {t(`status.${service.status}`)}
                </span>
              </div>
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">{t('status.latency')}</div>
              <div className="num mt-1 text-3xl font-semibold text-ink">
                {service.latencyMs !== undefined ? `${service.latencyMs} ms` : t('status.na')}
              </div>
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">{t('status.lastCheck')}</div>
              <div className="num mt-1 text-3xl font-semibold text-ink">
                {new Date(service.lastCheck).toLocaleString(locale)}
              </div>
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
            </Card>
            <Card density="compact">
              <div className="text-sm text-ink-soft">{t('status.source')}</div>
              <div className="num mt-1 text-3xl font-semibold text-ink">{provenance.source}</div>
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
            </Card>
          </div>
        </section>
      )}

      <section className="mx-auto max-w-5xl px-6 py-6">
        <h2 className="text-sm font-semibold text-ink-soft">{t('capabilities.title')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('capabilities.description')}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {service?.capabilities?.map((cap, idx) => (
            <Card key={idx} className="p-4 hover:border-water transition-colors">
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
              <p className="mt-2 text-sm text-ink">{cap}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6">
        <h2 className="text-sm font-semibold text-ink-soft">{t('endpoints.title')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('endpoints.description')}</p>
        <div className="mt-4 space-y-2">
          {service?.endpoints?.map((ep, idx) => (
            <Link key={idx} href={`/developers/api?endpoint=${encodeURIComponent(ep)}`} className="card p-3 hover:border-water transition-colors flex items-center justify-between">
              <code className="text-sm font-mono text-ink">{ep}</code>
              <ProvenanceStamp source={provenance.source} verified={provenance.verified} timestamp={provenance.timestamp} method={provenance.method} />
            </Link>
          ))}
        </div>
      </section>

      <p className="mx-auto max-w-5xl px-6 mt-10 text-xs text-ink-soft">{t('provenance.note')}</p>
      <OwnerFooter />
    </main>
  );
}