'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function BazaarAnalyticsPage() {
  const params = useParams();
  const locale = params.locale as string;
  const bazaarId = (params.id as string) ?? '';
  const t = useTranslations('market.bazaarAnalytics');

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
            <ProvenanceStamp source="bazaar-analytics" label="بازارچه — آنالیتیکس">
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {t('title', { id: bazaarId })}
              </h1>
            </ProvenanceStamp>
          </div>
<div className="flex gap-2">
            <Button variant="ghost">{t('exportCSV')}</Button>
            <Button variant="ghost">{t('exportPDF')}</Button>
          </div>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="grid gap-4 mb-8">
          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('trafficOverview')}</h3>
            <div className="grid gap-2 sm:grid-cols-4">
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-primary">12,450</p>
                <p className="text-xs text-ink-soft">{t('monthlyVisitors')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-forest">3,200</p>
                <p className="text-xs text-ink-soft">{t('uniqueCustomers')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-amber">4.2</p>
                <p className="text-xs text-ink-soft">{t('avgSessionMin')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-success">68%</p>
                <p className="text-xs text-ink-soft">{t('returnRate')}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('salesOverview')}</h3>
            <div className="grid gap-2 sm:grid-cols-4">
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-forest">890,000,000</p>
                <p className="text-xs text-ink-soft">{t('monthlyGMV')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-primary">1,850</p>
                <p className="text-xs text-ink-soft">{t('ordersCount')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-amber">481,000</p>
                <p className="text-xs text-ink-soft">{t('avgOrderValue')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-success">23%</p>
                <p className="text-xs text-ink-soft">{t('growthMom')}</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid gap-4">
          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('topCategories')}</h3>
            <div className="space-y-2">
              {[
                { name: t('cat.nuts'), sales: '320M', growth: '+15%' },
                { name: t('cat.spices'), sales: '280M', growth: '+28%' },
                { name: t('cat.honey'), sales: '150M', growth: '+8%' },
                { name: t('cat.driedFruit'), sales: '95M', growth: '+12%' },
                { name: t('cat.condiments'), sales: '45M', growth: '-3%' },
              ].map((cat, i) => (
                <div key={i} className="flex items-center justify-between p-2">
                  <span className="text-sm text-ink">{cat.name}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="font-mono text-ink-soft">{cat.sales}</span>
                    <span className={`font-medium ${cat.growth.startsWith('-') ? 'text-error' : 'text-success'}`}>
                      {cat.growth}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('topStores')}</h3>
            <div className="space-y-2">
              {[
                { name: 'فروشگاه آویز', revenue: '180M', orders: 420 },
                { name: 'زعفران طلایی', revenue: '150M', orders: 280 },
                { name: 'عسل طبیعی', revenue: '95M', orders: 190 },
                { name: 'گل‌قلیان سبز', revenue: '65M', orders: 150 },
              ].map((store, i) => (
                <div key={i} className="flex items-center justify-between p-2">
                  <span className="text-sm text-ink">{store.name}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="font-mono text-ink-soft">{store.revenue}</span>
                    <span className="text-ink-soft">{store.orders} {t('orders')}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}