import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface BulkOption {
  id: string;
  quantity: string;
  unit: string;
  price: number;
  minOrder: number;
  stock: number;
  discount: number;
}

const MOCK_BULK: BulkOption[] = [
  { id: 'b1', quantity: '5 kg', unit: 'kg', price: 1180000, minOrder: 5, stock: 12, discount: 3 },
  { id: 'b2', quantity: '25 kg', unit: 'kg', price: 5750000, minOrder: 25, stock: 5, discount: 8 },
  { id: 'b3', quantity: '50 kg', unit: 'kg', price: 11250000, minOrder: 50, stock: 2, discount: 12 },
  { id: 'b4', quantity: '100 kg', unit: 'kg', price: 22000000, minOrder: 100, stock: 1, discount: 15 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'خرید عمده', en: 'Bulk Purchase' };
  const descriptions: Record<string, string> = { fa: 'قیمت‌گذاری و گزینه‌های خرید انبوه', en: 'Wholesale pricing and bulk options' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/bulk`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/bulk`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/bulk`, en: `${BASE_URL}/en/market/product/${id}/bulk` } },
  };
}

export default async function BulkPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.bulk');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Bulk Pricing Engine" label={t('provenanceLabel')} verified={true} method="Tiered pricing" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('quantity')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('unitPrice')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('totalPrice')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('discount')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('minOrder')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('stock')}</th>
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('action')}</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_BULK.map(b => (
                <tr key={b.id} className="border-b border-line/50">
                  <td className="py-3 px-3 font-medium text-ink">{b.quantity}</td>
                  <td className="py-3 px-3 text-ink-soft">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(Math.round(b.price / parseInt(b.quantity)))} ریال/{b.unit}</td>
                  <td className="py-3 px-3 font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(b.price)} ریال</td>
                  <td className="py-3 px-3"><span className="px-2 py-1 rounded bg-forest/10 text-forest text-xs font-medium">{b.discount}%</span></td>
                  <td className="py-3 px-3 text-ink-soft">{b.minOrder} {b.unit}</td>
                  <td className="py-3 px-3">
                    <StatusDot state={b.stock > 0 ? 'ok' : 'down'} label={b.stock > 0 ? common('inStock') : common('outOfStock')} />
                  </td>
                  <td className="py-3 px-3">
                    <Button variant="primary" size="sm">{t('addToCart')}</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4">
          <ProvenanceStamp source="Bulk Pricing Engine" verified={true} method="Tiered" label="Bulk pricing provenance" />
        </div>
      </section>
    </main>
  );
}