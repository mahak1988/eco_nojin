'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function BazaarFinancesPage() {
  const params = useParams();
  const locale = params.locale as string;
  const id = params.id as string;
  const bazaarId = id ?? '';
  const t = useTranslations('market.bazaarFinances');

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
            <ProvenanceStamp source="bazaar-finances" label="بازارچه — مالی">
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {t('title', { id: bazaarId })}
              </h1>
            </ProvenanceStamp>
          </div>
          <Button variant="ghost">{t('exportReport')}</Button>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="grid gap-4 mb-8">
          <Card className="p-4">
            <div className="grid gap-2 sm:grid-cols-4">
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-forest">1,250,000,000</p>
                <p className="text-xs text-ink-soft">{t('totalRevenue')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-primary">420,000,000</p>
                <p className="text-xs text-ink-soft">{t('monthlyRevenue')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-amber">180,000,000</p>
                <p className="text-xs text-ink-soft">{t('pendingPayments')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-success">650,000,000</p>
                <p className="text-xs text-ink-soft">{t('netProfit')}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-medium text-ink mb-3">{t('revenueBreakdown')}</h3>
            <div className="space-y-2">
              {[
                { label: t('stallRent'), value: '65%', color: 'forrest' },
                { label: t('commissionFees'), value: '25%', color: 'primary' },
                { label: t('serviceFees'), value: '8%', color: 'amber' },
                { label: t('other'), value: '2%', color: 'ink-soft' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: `var(--${item.color})` }} />
                  <span className="flex-1 text-sm text-ink">{item.label}</span>
                  <span className="text-sm font-mono text-ink-soft">{item.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="font-medium text-ink mb-4">{t('recentTransactions')}</h3>
          <div className="space-y-3">
            {[
              { date: '2025-07-10', desc: t('tx1'), amount: '+45,000,000', type: 'credit' },
              { date: '2025-07-08', desc: t('tx2'), amount: '-12,500,000', type: 'debit' },
              { date: '2025-07-05', desc: t('tx3'), amount: '+78,000,000', type: 'credit' },
              { date: '2025-07-01', desc: t('tx4'), amount: '-8,200,000', type: 'debit' },
            ].map((tx, i) => (
              <div key={i} className="flex items-center justify-between p-3 border-b last:border-0">
                <div>
                  <p className="font-medium text-ink">{tx.desc}</p>
                  <p className="text-xs text-ink-soft">{tx.date}</p>
                </div>
                <span className={`font-mono ${tx.type === 'credit' ? 'text-success' : 'text-error'}`}>
                  {tx.amount} ریال
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}