import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface DisputeEvidence {
  id: string;
  type: 'photo' | 'document' | 'video';
  description: string;
  uploadedBy: string;
  timestamp: string;
}

const MOCK_EVIDENCE: DisputeEvidence[] = [
  { id: 'e1', type: 'photo', description: 'تصویر محصول تحویل شده', uploadedBy: 'خریدار', timestamp: '2024-12-13T10:30:00Z' },
  { id: 'e2', type: 'document', description: 'رسید تحویل پست', uploadedBy: 'فروشنده', timestamp: '2024-12-11T09:00:00Z' },
  { id: 'e3', type: 'photo', description: 'تصویر بسته‌بندی', uploadedBy: 'فروشنده', timestamp: '2024-12-11T09:15:00Z' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'مرکز منازعات', en: 'Dispute Center' };
  const descriptions: Record<string, string> = { fa: 'مدیریت و حل اختلافات سفارش', en: 'Manage and resolve order disputes' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/orders/${id}/dispute`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/orders/${id}/dispute`, languages: { fa: `${BASE_URL}/fa/market/orders/${id}/dispute`, en: `${BASE_URL}/en/market/orders/${id}/dispute` } },
  };
}

export default async function DisputePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.orders.dispute');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/orders/${id}`} className="underline hover:text-ink">{common('backToOrder')}</a>
        </nav>
        <ProvenanceStamp source="Dispute Service" label={t('provenanceLabel')} verified={true} method="Arbitration-logged" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Evidence-based', '3-arbitrator panel', 'Escrow-linked enforcement']}
          limits={['14-day window', 'Binding decision', 'Appeal to bazaar']}
          next={['Submit evidence', 'Select arbitrators', 'Await verdict']}
          evidenceLabel="Evidence" limitsLabel="Limits" nextLabel="Next"
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <StatusDot state="warn" label={t('underReview')} />
          </div>
        </div>

        <Card density="cozy">
          <h2 className="font-semibold text-ink mb-4">{t('disputeReason')}</h2>
          <p className="text-ink-soft mb-4">{t('disputeReasonDesc')}</p>

          <h3 className="font-semibold text-ink mb-3">{t('evidence')}</h3>
          <div className="space-y-3">
            {MOCK_EVIDENCE.map(e => (
              <Card key={e.id} density="compact">
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 rounded flex items-center justify-center bg-slate/10">
                    {e.type === 'photo' && '📷'}
                    {e.type === 'document' && '📄'}
                    {e.type === 'video' && '🎥'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-ink">{e.description}</p>
                    <p className="text-xs text-ink-soft">توسط {e.uploadedBy} · {new Date(e.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className="mt-4 flex gap-3">
            <Button variant="primary" className="flex-1">{t('addEvidence')}</Button>
            <Button variant="ghost">{t('requestMediation')}</Button>
          </div>
        </Card>

        <Card density="cozy" className="mt-4">
          <h2 className="font-semibold text-ink mb-4">{t('arbitrationStatus')}</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-ink-soft">{t('panelStatus')}</span><StatusDot state="warn" label={t('forming')} /></div>
            <div className="flex justify-between"><span className="text-ink-soft">{t('deadline')}</span><span className="text-ink">2024-12-20</span></div>
          </div>
        </Card>
      </section>
    </main>
  );
}