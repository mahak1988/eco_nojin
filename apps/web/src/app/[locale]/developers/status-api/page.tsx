'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';

interface HealthCheck {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  latency: number;
  lastCheck: string;
}

interface QuotaInfo {
  used: number;
  limit: number;
  resetAt: string;
}

export default function StatusApiPage() {
  const t = useTranslations('developers.statusApi');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [health, setHealth] = useState<HealthCheck[]>([]);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [healthRes, quotaRes] = await Promise.all([
          fetch(`/api/developers/health?locale=${locale}`),
          fetch(`/api/developers/quota?locale=${locale}`),
        ]);
        if (!healthRes.ok || !quotaRes.ok) throw new Error('Failed to fetch');
        const healthData = await healthRes.json();
        const quotaData = await quotaRes.json();
        setHealth(healthData.services || []);
        setQuota(quotaData);
      } catch (err) {
        setError(t('fetchError'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [locale, t]);

  if (isLoading) {
    return (
      <main id="main" className="min-h-screen">
        <div className="mx-auto max-w-4xl px-4 py-10">
          <div className="text-center py-20">
            <p className="text-ink-soft">{t('loading')}</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
            <p className="mt-3 text-ink-soft">{t('lead')}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusDot state="ok" label={t('status.healthy')} />
            <span className="text-sm text-ink-soft">{t('lastUpdated', { time: new Date().toLocaleTimeString() })}</span>
          </div>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700" role="alert">
            {error}
          </div>
        )}

        {quota && (
          <Card density="cozy" className="mb-6">
            <h2 className="font-medium text-ink mb-4">{t('quota')}</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="card p-4">
                <p className="text-sm text-ink-soft">{t('quota.used')}</p>
                <p className="num mt-1 text-3xl font-semibold text-ink">{quota.used.toLocaleString()}</p>
              </div>
              <div className="card p-4">
                <p className="text-sm text-ink-soft">{t('quota.limit')}</p>
                <p className="num mt-1 text-3xl font-semibold text-ink">{quota.limit.toLocaleString()}</p>
              </div>
              <div className="card p-4">
                <p className="text-sm text-ink-soft">{t('quota.remaining')}</p>
                <p className="num mt-1 text-3xl font-semibold text-ink">
                  {(quota.limit - quota.used).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="mt-4">
              <div className="h-2 bg-line rounded-full overflow-hidden">
                <div
                  className="h-full bg-forest rounded-full transition-all duration-300"
                  style={{ width: `${(quota.used / quota.limit) * 100}%` }}
                />
              </div>
              <p className="mt-1 text-sm text-ink-soft">
                {t('quota.resetsAt', { time: new Date(quota.resetAt).toLocaleString(locale === 'fa' ? 'fa-IR' : 'en-US') })}
              </p>
            </div>
          </Card>
        )}

<Card density="compact">
          <h2 className="font-medium text-ink mb-3">{t('services')}</h2>
          <div className="space-y-3">
            {health.map((svc) => {
              const stateMap: Record<string, 'ok' | 'warn' | 'down'> = {
                healthy: 'ok',
                degraded: 'warn',
                down: 'down',
              };
              return (
                <div key={svc.service} className="flex items-center justify-between p-3 card">
                  <div className="flex items-center gap-3">
                    <StatusDot state={stateMap[svc.status] || 'down'} label={t(`status.${svc.status}`)} />
                    <div>
                      <p className="font-medium text-ink">{svc.service}</p>
                      <p className="text-xs text-ink-soft">
                        {t('lastCheck', { time: new Date(svc.lastCheck).toLocaleTimeString() })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      svc.status === 'healthy' ? 'bg-forest/10 text-forest' :
                      svc.status === 'degraded' ? 'bg-copper/10 text-copper' :
                      'bg-red/10 text-red'
                    }`}>
                      {t(`status.${svc.status}`)}
                    </span>
                    <span className="text-ink-soft font-mono">
                      {svc.latency}ms
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          <ProvenanceStamp source="Health Check" verified={true} method="Automated" />
        </Card>

        <div className="mt-6 grid gap-4">
          <Card density="cozy" className="border-clay/40 bg-clay/5">
            <h3 className="font-medium text-ink mb-2">{t('limitsTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('limits')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-copper">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card density="cozy" className="border-forest/40 bg-forest/5">
            <h3 className="font-medium text-ink mb-2">{t('nextTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('next')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-forest">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </main>
  );
}