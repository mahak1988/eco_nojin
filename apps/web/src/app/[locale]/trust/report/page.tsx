'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface ReportData {
  year: number;
  totalProjects: number;
  totalCarbonCredits: number;
  totalUsers: number;
  keyMetrics: Array<{ label: string; value: string; change?: string }>;
  charts: {
    projectsByRegion: Array<{ region: string; count: number }>;
    carbonByMonth: Array<{ month: string; amount: number }>;
  };
}

export default function ReportPage() {
  const t = useTranslations('trust.report');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1];

  const [report, setReport] = useState<ReportData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchReport() {
      try {
        const res = await fetch(`/api/trust/report?locale=${locale}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setReport(data);
      } catch (err) {
        setError(t('fetchError'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchReport();
  }, [locale, t]);

  const n = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

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

  if (!report) {
    return (
      <main id="main" className="min-h-screen">
        <div className="mx-auto max-w-4xl px-4 py-10">
          <Card density="cozy" className="text-center py-8">
            <p className="text-ink-soft">{t('noData')}</p>
          </Card>
        </div>
      </main>
    );
  }

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { year: report.year })}</h1>
            <p className="mt-3 text-ink-soft">{t('lead')}</p>
          </div>
          <Button variant="secondary" onClick={() => window.print()}>
            {t('downloadPdf')}
          </Button>
        </header>

        <ProvenanceStamp
          source="Annual Report"
          verified={true}
          timestamp={new Date(`${report.year}-12-31`).toISOString()}
          method="Aggregated from platform data"
        />

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card density="cozy">
            <p className="text-sm text-ink-soft">{t('metrics.totalProjects')}</p>
            <p className="num mt-1 text-3xl font-semibold text-ink">{n.format(report.totalProjects)}</p>
          </Card>
          <Card density="cozy">
            <p className="text-sm text-ink-soft">{t('metrics.totalCarbonCredits')}</p>
            <p className="num mt-1 text-3xl font-semibold text-ink">{n.format(report.totalCarbonCredits)}</p>
          </Card>
          <Card density="cozy">
            <p className="text-sm text-ink-soft">{t('metrics.totalUsers')}</p>
            <p className="num mt-1 text-3xl font-semibold text-ink">{n.format(report.totalUsers)}</p>
          </Card>
          <Card density="cozy">
            <p className="text-sm text-ink-soft">{t('metrics.year')}</p>
            <p className="num mt-1 text-3xl font-semibold text-ink">{report.year}</p>
          </Card>
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-4">{t('keyMetrics')}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {report.keyMetrics.map((metric, idx) => (
              <div key={idx} className="card p-4">
                <p className="text-sm text-ink-soft">{metric.label}</p>
                <p className="num mt-1 text-2xl font-semibold text-ink">{metric.value}</p>
                {metric.change && (
                  <p className={`mt-1 text-sm ${metric.change.startsWith('+') ? 'text-forest' : 'text-copper'}`}>
                    {metric.change}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card density="cozy">
            <h2 className="font-medium text-ink mb-4">{t('charts.projectsByRegion')}</h2>
            <div className="h-64 flex items-end gap-2 justify-center">
              {report.charts.projectsByRegion.map((item, idx) => (
                <div key={idx} className="flex flex-col items-center flex-1">
                  <div
                    className="w-full bg-forest rounded-t transition-all duration-300"
                    style={{ height: `${(item.count / Math.max(...report.charts.projectsByRegion.map(r => r.count))) * 100}%` }}
                  />
                  <p className="mt-2 text-xs text-ink-soft text-center">{item.region}</p>
                  <p className="text-sm font-mono text-ink">{n.format(item.count)}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card density="cozy">
            <h2 className="font-medium text-ink mb-4">{t('charts.carbonByMonth')}</h2>
            <div className="h-64 flex items-end gap-2 justify-center">
              {report.charts.carbonByMonth.map((item, idx) => (
                <div key={idx} className="flex flex-col items-center flex-1">
                  <div
                    className="w-full bg-water rounded-t transition-all duration-300"
                    style={{ height: `${(item.amount / Math.max(...report.charts.carbonByMonth.map(r => r.amount))) * 100}%` }}
                  />
                  <p className="mt-2 text-xs text-ink-soft text-center">{item.month}</p>
                  <p className="text-sm font-mono text-ink">{n.format(item.amount)}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>

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