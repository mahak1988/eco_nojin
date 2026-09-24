'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

export default function BazaarSupervisionPage() {
  const params = useParams();
  const { locale, id } = params;
  const bazaarId = (Array.isArray(id) ? id[0] : id) ?? '';
  const t = useTranslations('market.bazaarSupervision');

  const mockInspections = [
    { id: 'i001', date: '2025-07-01', inspector: 'سازمان صنایع روستایی', result: 'passed', notes: 'همه معايير برآورده شد' },
    { id: 'i002', date: '2025-04-15', inspector: 'وزارت جهاد کشاورزی', result: 'warning', notes: 'نیاز به بهبود انباردهی' },
    { id: 'i003', date: '2025-01-20', inspector: 'سازمان معايير', result: 'passed', notes: 'بدون یادداشت' },
  ];

  const mockCompliance = [
    { area: 'health_safety', score: 92, status: 'ok' },
    { area: 'environmental', score: 78, status: 'warn' },
    { area: 'labor_standards', score: 85, status: 'ok' },
    { area: 'financial_transparency', score: 88, status: 'ok' },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <a
              href={`/${locale}/market/bazaars/${bazaarId}`}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
            </a>
          </nav>
          <ProvenanceStamp source="bazaar-supervision" label="بازارچه — نظارت">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {t('title', { id: bazaarId })}
            </h1>
          </ProvenanceStamp>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="grid gap-4 mb-8">
          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('complianceScores')}</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {mockCompliance.map(item => (
                <div key={item.area} className="p-3 border rounded">
                  <p className="text-sm text-ink-soft capitalize">{item.area.replace('_', ' ')}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-2 bg-surface rounded overflow-hidden">
                      <div
                        className="h-full"
                        style={{
                          width: `${item.score}%`,
                          backgroundColor: item.status === 'ok' ? 'var(--success)' : 'var(--warning)'
                        }}
                      />
                    </div>
                    <span className="font-mono text-sm font-bold">{item.score}%</span>
                    <StatusDot state={item.status === 'ok' ? 'ok' : 'warn'} label="" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('nextInspection')}</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{t('scheduledDate')}</p>
                <p className="text-sm text-ink-soft">2025-10-15</p>
              </div>
              <StatusDot state="warn" label={t('upcoming')} />
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="font-medium text-ink mb-4">{t('inspectionHistory')}</h3>
          <div className="space-y-3">
            {mockInspections.map(insp => (
              <div key={insp.id} className="flex items-center justify-between p-3 border-b last:border-0">
                <div>
                  <p className="font-medium text-ink">{insp.inspector}</p>
                  <p className="text-sm text-ink-soft">{insp.date} — {insp.notes}</p>
                </div>
                <StatusDot
                  state={insp.result === 'passed' ? 'ok' : insp.result === 'warning' ? 'warn' : 'down'}
                  label={t('result.' + insp.result)}
                />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}