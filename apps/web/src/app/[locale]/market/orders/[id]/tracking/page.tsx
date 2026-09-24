import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'پیگیری ارسال', en: 'Shipment Tracking' };
  const descriptions: Record<string, string> = { fa: 'پیگیری بسته تا تحویل', en: 'Track shipment to delivery' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/orders/${id}/tracking`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/orders/${id}/tracking`, languages: { fa: `${BASE_URL}/fa/market/orders/${id}/tracking`, en: `${BASE_URL}/en/market/orders/${id}/tracking` } },
  };
}

export default async function TrackingPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.orders.tracking');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/orders/${id}`} className="underline hover:text-ink">{common('backToOrder')}</a>
        </nav>
        <ProvenanceStamp source="Logistics Service" label={t('provenanceLabel')} verified={true} method="Carrier API" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real-time carrier API', 'Multi-carrier support', 'SMS notifications']}
          limits={['Carrier API limits', 'International gaps', 'Offline mode limited']}
          next={['Add map view', 'Enable webhook', 'Predictive ETA']}
          evidenceLabel="Evidence" limitsLabel="Limits" nextLabel="Next"
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <h2 className="font-semibold text-ink mb-4">{t('trackingInfo')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('trackingNumber')}</span>
              <code className="font-mono text-ink">IRPST1234567890</code>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('carrier')}</span>
              <span className="text-ink">پست پیشتاز ایران</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('status')}</span>
              <StatusDot state="ok" label={t('inTransit')} />
            </div>
            <div className="flex justify-between">
              <span className="text-ink-soft">{t('estimatedDelivery')}</span>
              <span className="font-medium text-ink">2024-12-13</span>
            </div>
          </div>
        </Card>

        <Card density="cozy" className="mt-4">
          <h2 className="font-semibold text-ink mb-4">{t('milestones')}</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-forest/5 rounded">
              <span className="w-8 h-8 rounded-full flex items-center justify-center bg-forest text-paper">✓</span>
              <div>
                <p className="font-medium text-ink">{t('pickedUp')}</p>
                <p className="text-sm text-ink-soft">2024-12-11 09:00</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-forest/5 rounded">
              <span className="w-8 h-8 rounded-full flex items-center justify-center bg-forest text-paper">✓</span>
              <div>
                <p className="font-medium text-ink">{t('inTransit')}</p>
                <p className="text-sm text-ink-soft">2024-12-11 14:30 - مرکز پردازش تهران</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-forest/5 rounded">
              <span className="w-8 h-8 rounded-full flex items-center justify-center bg-forest text-paper">✓</span>
              <div>
                <p className="font-medium text-ink">{t('outForDelivery')}</p>
                <p className="text-sm text-ink-soft">2024-12-13 08:00 - پیک در مسیر</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded">
              <span className="w-8 h-8 rounded-full flex items-center justify-center bg-slate/10 text-slate">○</span>
              <div>
                <p className="font-medium text-ink-soft">{t('delivered')}</p>
                <p className="text-sm text-ink-soft">منتظر تحویل</p>
              </div>
            </div>
          </div>
        </Card>

        <Button variant="primary" className="w-full mt-4" onClick={() => window.location.href = `/${locale}/market/orders/${id}/delivery`}>
          {t('confirmDelivery')}
        </Button>
      </section>
    </main>
  );
}