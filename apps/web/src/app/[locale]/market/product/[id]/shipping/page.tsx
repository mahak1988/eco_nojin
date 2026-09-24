import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface ShippingOption {
  id: string;
  name: { fa: string; en: string };
  description: string;
  deliveryTime: string;
  cost: number;
  freeThreshold: number;
  available: boolean;
}

const MOCK_SHIPPING: ShippingOption[] = [
  { id: 's1', name: { fa: 'استاندارد', en: 'Standard' }, description: 'ارسال پستی معمولی', deliveryTime: '5-7 روز کاری', cost: 50000, freeThreshold: 5000000, available: true },
  { id: 's2', name: { fa: 'اکسپرس', en: 'Express' }, description: 'ارسال سریع با پیک', deliveryTime: '1-2 روز کاری', cost: 150000, freeThreshold: 10000000, available: true },
  { id: 's3', name: { fa: 'باربری', en: 'Freight' }, description: 'برای سفارشات انبوه', deliveryTime: '3-5 روز کاری', cost: 0, freeThreshold: 50000000, available: true },
  { id: 's4', name: { fa: 'تحویل در محل', en: 'Pickup' }, description: 'دریافت از انبار مرکزی', deliveryTime: 'بلافاصله', cost: 0, freeThreshold: 0, available: false },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'گزینه‌های ارسال', en: 'Shipping Options' };
  const descriptions: Record<string, string> = { fa: 'روش‌ها و هزینه‌های ارسال', en: 'Shipping methods and costs' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/shipping`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/shipping`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/shipping`, en: `${BASE_URL}/en/market/product/${id}/shipping` } },
  };
}

export default async function ShippingPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  const loc = locale as string;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.shipping');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Logistics Engine" label={t('provenanceLabel')} verified={true} method="Carrier API" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="grid gap-4 sm:grid-cols-2">
          {MOCK_SHIPPING.map(opt => {
            const optName = opt.name as Record<string, string>;
            return (
              <Card key={opt.id} density="cozy">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-ink">{optName[loc] ?? optName.fa}</h3>
                    <p className="text-sm text-ink-soft mt-1">{opt.description}</p>
                    <p className="text-xs text-ink-soft mt-1">{t('deliveryTime')}: {opt.deliveryTime}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-forest">{opt.cost === 0 ? t('free') : new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(opt.cost) + ' ریال'}</p>
                    <p className="text-xs text-ink-soft">{t('freeOver')}: {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(opt.freeThreshold)} ریال</p>
                    <StatusDot state={opt.available ? 'ok' : 'down'} label={opt.available ? common('available') : common('unavailable')} />
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-line">
                  <Button variant="primary" size="sm" className="w-full" disabled={!opt.available}>{opt.available ? t('select') : t('unavailable')}</Button>
                </div>
              </Card>
            );
          })}
        </div>
        <div className="mt-4">
          <ProvenanceStamp source="Logistics Engine" verified={true} method="Carrier API" label="Shipping provenance" />
        </div>
      </section>
    </main>
  );
}