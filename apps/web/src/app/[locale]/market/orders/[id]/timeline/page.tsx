import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface TimelineEvent {
  id: string;
  timestamp: string;
  status: string;
  description: string;
  actor: string;
}

const MOCK_EVENTS: TimelineEvent[] = [
  { id: 'e1', timestamp: '2024-12-10T10:30:00Z', status: 'created', description: 'سفارش ایجاد شد', actor: 'خریدار' },
  { id: 'e2', timestamp: '2024-12-10T11:00:00Z', status: 'escrow_locked', description: 'اسکرو قفل شد', actor: 'پلتفرم' },
  { id: 'e3', timestamp: '2024-12-10T14:00:00Z', status: 'processing', description: 'توسط تولیدکننده در حال پردازش', actor: 'فروشنده' },
  { id: 'e4', timestamp: '2024-12-11T09:00:00Z', status: 'shipped', description: 'ارسال شده از طریق پست پیشتاز', actor: 'فروشنده' },
  { id: 'e5', timestamp: '2024-12-13T10:30:00Z', status: 'delivered', description: 'تحویل به خریدار', actor: 'پیک' },
  { id: 'e6', timestamp: '2024-12-13T11:00:00Z', status: 'confirmed', description: 'تحویل تأیید شد', actor: 'خریدار' },
  { id: 'e7', timestamp: '2024-12-13T12:00:00Z', status: 'released', description: 'اسکرو آزاد شد', actor: 'پلتفرم' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'خط زمان سفارش', en: 'Order Timeline' };
  const descriptions: Record<string, string> = { fa: 'مشاهده رویدادهای سفارش', en: 'View order events timeline' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/orders/${id}/timeline`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/orders/${id}/timeline`, languages: { fa: `${BASE_URL}/fa/market/orders/${id}/timeline`, en: `${BASE_URL}/en/market/orders/${id}/timeline` } },
  };
}

export default async function TimelinePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.orders.timeline');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/orders`} className="underline hover:text-ink">{common('backToOrders')}</a>
        </nav>
        <ProvenanceStamp source="Timeline Service" label={t('provenanceLabel')} verified={true} method="Event-sourced" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Event-sourced', 'Immutable log', 'Real-time updates']}
          limits={['Offline events delayed', 'Timezone display', 'Actor verification']}
          next={['Add notifications', 'Enable webhook', 'Export timeline']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <div className="space-y-4">
          {MOCK_EVENTS.map(event => (
            <Card key={event.id} density="compact">
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-forest/10 text-forest">
                    <StatusDot state="ok" label="" />
                  </div>
                  <div className="w-px h-full bg-line mx-auto" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{event.description}</h3>
                    <span className="px-2 py-0.5 rounded text-xs bg-forest/10 text-forest">{event.status}</span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{new Date(event.timestamp).toLocaleString(locale === 'fa' ? 'fa-IR' : 'en-US')}</p>
                  <p className="text-xs text-ink-soft">{event.actor}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}