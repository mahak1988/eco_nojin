'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';

export default function BazaarDisputesPage() {
  const params = useParams();
  const locale = params.locale as string;
  const id = params.id as string;
  const bazaarId = id ?? '';
  const t = useTranslations('market.bazaarDisputes');

  const mockDisputes = [
    { id: 'd001', title: 'اختلاف در اجاره Staion 3', parties: 'فروشگاه آویز vs مدیریت', status: 'mediation', filed: '2025-07-01' },
    { id: 'd002', title: 'نقص کالا - زعفران', parties: 'خریدار vs زعفران طلایی', status: 'resolved', filed: '2025-06-15' },
    { id: 'd003', title: 'تاخیر در پرداخت کمیسیون', parties: 'مدیریه vs فروشگاه عسل', status: 'open', filed: '2025-07-10' },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <nav className="mb-4">
              <a
                href={`/${locale}/market/bazaars/${bazaarId}`}
                className="text-sm text-ink-soft hover:text-ink underline"
              >
                ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
              </a>
            </nav>
            <ProvenanceStamp source="bazaar-disputes" label="بازارچه — اختلافات">
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {t('title', { id: bazaarId })}
              </h1>
            </ProvenanceStamp>
          </div>
          <Button>{t('fileDispute')}</Button>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="grid gap-4 mb-8">
          <Card className="p-4">
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-error">3</p>
                <p className="text-xs text-ink-soft">{t('openDisputes')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-warning">2</p>
                <p className="text-xs text-ink-soft">{t('inMediation')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-success">12</p>
                <p className="text-xs text-ink-soft">{t('resolvedThisYear')}</p>
              </div>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="font-medium text-ink mb-4">{t('disputeList')}</h3>
          <div className="space-y-3">
            {mockDisputes.map(dispute => (
              <div key={dispute.id} className="flex items-center justify-between p-4 border-b last:border-0">
                <div>
                  <h4 className="font-medium text-ink">{dispute.title}</h4>
                  <p className="text-sm text-ink-soft">{dispute.parties} — {t('filed')}: {dispute.filed}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot
                    state={dispute.status === 'open' ? 'down' : dispute.status === 'mediation' ? 'warn' : 'ok'}
                    label={t('status.' + dispute.status)}
                  />
                  <Button variant="ghost" size="sm">{t('view')}</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}