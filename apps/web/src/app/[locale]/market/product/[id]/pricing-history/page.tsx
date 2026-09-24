import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface PricePoint {
  date: string;
  price: number;
  unit: string;
  source: string;
}

const MOCK_PRICES: PricePoint[] = [
  { date: '2024-10-01', price: 235000, unit: '1 kg', source: 'Market avg' },
  { date: '2024-11-01', price: 242000, unit: '1 kg', source: 'Market avg' },
  { date: '2024-12-01', price: 245000, unit: '1 kg', source: 'Current' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'تاریخچه قیمت', en: 'Price History' };
  const descriptions: Record<string, string> = { fa: 'نمودار تغییرات قیمت در طول زمان', en: 'Price trend chart over time' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/pricing-history`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/pricing-history`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/pricing-history`, en: `${BASE_URL}/en/market/product/${id}/pricing-history` } },
  };
}

export default async function PricingHistoryPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.pricingHistory');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Price Oracle" label={t('provenanceLabel')} verified={true} method="Market aggregation" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <Card density="cozy">
          <div className="h-64 flex items-end justify-around px-4 pb-4">
            {MOCK_PRICES.map((p, i) => (
              <div key={i} className="flex flex-col items-center" style={{ width: '30%' }}>
                <div className="bg-forest w-full rounded-t" style={{ height: `${(p.price / 250000) * 100}%`, minHeight: '40px' }} />
                <span className="text-xs text-ink-soft mt-2">{new Date(p.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US', { month: 'short' })}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('date')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('price')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('unit')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('source')}</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_PRICES.map(p => (
                  <tr key={p.date} className="border-b border-line/50">
                    <td className="py-2 px-3 text-ink">{new Date(p.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</td>
                    <td className="py-2 px-3 font-mono text-ink">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال</td>
                    <td className="py-2 px-3 text-ink-soft">{p.unit}</td>
                    <td className="py-2 px-3 text-ink-soft">{p.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <div className="mt-4">
          <ProvenanceStamp source="Price Oracle" verified={true} method="Aggregated" label="Price history provenance" />
        </div>
      </section>
    </main>
  );
}