'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

export default function BazaarGovernancePage() {
  const params = useParams();
  const { locale, id } = params;
  const bazaarId = (Array.isArray(id) ? id[0] : id) ?? '';
  const t = useTranslations('market.bazaarGovernance');

  const mockProposals = [
    { id: 'p001', title: 'افزایش سهمیه فروشگاه‌ها', status: 'voting', votes: '12/5', deadline: '2025-07-15' },
    { id: 'p002', title: 'تغییر ساعات کاری', status: 'passed', votes: '15/2', deadline: '2025-06-20' },
    { id: 'p003', title: 'مصوبنامه جدید عضویت', status: 'pending', votes: '0/0', deadline: '2025-08-01' },
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
          <ProvenanceStamp source="bazaar-governance" label="بازارچه — حکمرانی">
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
            <h3 className="font-medium text-ink mb-2">{t('boardMembers')}</h3>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }, (_, i) => (
                <div key={i} className="text-center p-3 border rounded">
                  <div className="w-12 h-12 rounded-full bg-primary/10 mx-auto mb-2 flex items-center justify-center text-primary font-bold">
                    {i + 1}
                  </div>
                  <p className="text-sm font-medium">{t('trustee', { num: i + 1 })}</p>
                  <p className="text-xs text-ink-soft">{t('role' + (i + 1))}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-medium text-ink mb-2">{t('keyMetrics')}</h3>
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-forest">5</p>
                <p className="text-xs text-ink-soft">{t('activeTrustees')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-primary">12</p>
                <p className="text-xs text-ink-soft">{t('pendingProposals')}</p>
              </div>
              <div className="text-center p-3 bg-surface-alt rounded">
                <p className="text-2xl font-bold text-amber">3</p>
                <p className="text-xs text-ink-soft">{t('activeDisputes')}</p>
              </div>
            </div>
          </Card>
        </div>

        <Card>
          <h3 className="font-medium text-ink mb-4">{t('proposals')}</h3>
          <div className="space-y-3">
            {mockProposals.map(proposal => (
              <div key={proposal.id} className="flex items-center justify-between p-4 border rounded">
                <div>
                  <h4 className="font-medium text-ink">{proposal.title}</h4>
                  <p className="text-sm text-ink-soft">{t('deadline')}: {proposal.deadline}</p>
                </div>
                <div className="flex items-center gap-4">
                  <StatusDot
                    state={proposal.status === 'voting' ? 'warn' : proposal.status === 'passed' ? 'ok' : 'down'}
                    label={t('status.' + proposal.status)}
                  />
                  <span className="text-sm font-mono text-ink-soft">{proposal.votes}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}