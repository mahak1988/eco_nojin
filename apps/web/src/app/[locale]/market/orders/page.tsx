import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Order {
  id: string;
  date: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'disputed';
  total: number;
  items: number;
  escrowId?: string;
}

const MOCK_ORDERS: Order[] = [
  { id: 'ORD-001', date: '2024-12-10', status: 'delivered', total: 12500000, items: 3, escrowId: 'ESC-001' },
  { id: 'ORD-002', date: '2024-12-08', status: 'shipped', total: 8900000, items: 1, escrowId: 'ESC-002' },
  { id: 'ORD-003', date: '2024-12-05', status: 'processing', total: 5200000, items: 2, escrowId: 'ESC-003' },
  { id: 'ORD-004', date: '2024-12-01', status: 'disputed', total: 3400000, items: 1, escrowId: 'ESC-004' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'سفارشات من', en: 'My Orders' };
  const descriptions: Record<string, string> = { fa: 'مشاهده و مدیریت سفارشات', en: 'View and manage orders' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/orders`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/orders`, languages: { fa: `${BASE_URL}/fa/market/orders`, en: `${BASE_URL}/en/market/orders` } },
  };
}

export default async function OrdersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.orders');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Orders Service" label={t('provenanceLabel')} verified={true} method="Escrow-signed" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real-time status', 'Escrow integration', 'Dispute resolution']}
          limits={['History limited to 2 years', 'Bulk export limited', 'International shipping not tracked']}
          next={['Add reorder button', 'Enable bulk actions', 'Add analytics']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="flex flex-wrap gap-2 mb-6">
          {['all', 'pending', 'processing', 'shipped', 'delivered', 'disputed'].map(f => (
            <button key={f} className="px-4 py-2 rounded-md text-sm font-medium bg-surface-alt text-ink-soft hover:text-ink">
              {f === 'all' ? common('all') : t(f)}
            </button>
          ))}
        </div>

        <div className="space-y-4">
          {MOCK_ORDERS.map(order => (
            <Card key={order.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{t('order')} #{order.id}</h3>
                    <StatusDot
                      state={order.status === 'delivered' ? 'ok' : order.status === 'shipped' ? 'ok' : order.status === 'processing' ? 'warn' : order.status === 'disputed' ? 'down' : 'warn'}
                      label={common(order.status)}
                    />
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{order.items} {t('items')} · {new Date(order.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</p>
                </div>
                <div className="text-right sm:text-left">
                  <p className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(order.total)} ریال</p>
                  {order.escrowId && (
                    <a href={`/${locale}/market/escrow/${order.escrowId}`} className="text-sm text-forest underline mt-1 block">
                      {t('viewEscrow')}: {order.escrowId}
                    </a>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-line">
                <button className="px-3 py-1.5 rounded border border-line text-sm text-ink-soft hover:bg-forest/5">{t('viewDetails')}</button>
                {order.status === 'delivered' && <button className="px-3 py-1.5 rounded border border-line text-sm text-ink-soft hover:bg-forest/5">{t('reorder')}</button>}
                {order.status === 'shipped' && <button className="px-3 py-1.5 rounded border border-line text-sm text-ink-soft hover:bg-forest/5">{t('confirmDelivery')}</button>}
                {order.status === 'disputed' && <button className="px-3 py-1.5 rounded border border-line text-sm text-copper hover:bg-copper/5">{t('viewDispute')}</button>}
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}