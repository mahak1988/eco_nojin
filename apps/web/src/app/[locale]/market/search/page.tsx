import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Product {
  id: string;
  name: { fa: string; en: string };
  producer: string;
  price: number;
  unit: string;
  category: string;
  organic: boolean;
  stock: number;
  rating: number;
}

const MOCK_PRODUCTS: Product[] = [
  { id: 'p1', name: { fa: 'پسته ارگانیک', en: 'Organic Pistachio' }, producer: 'Kerman Coop', price: 245000, unit: '1 kg', category: 'Nuts', organic: true, stock: 42, rating: 4.8 },
  { id: 'p2', name: { fa: 'زعفران سوپر نگین', en: 'Super Negin Saffron' }, producer: 'Khorasan Farm', price: 8900000, unit: '5 g', category: 'Spices', organic: true, stock: 8, rating: 4.9 },
  { id: 'p3', name: { fa: 'بادام ممان', en: 'Maman Almonds' }, producer: 'Gilan Co-op', price: 185000, unit: '500 g', category: 'Nuts', organic: true, stock: 25, rating: 4.6 },
  { id: 'p4', name: { fa: 'خرما مضافتی', en: 'Mazafati Dates' }, producer: 'Bam Dates', price: 125000, unit: '1 kg', category: 'Dried Fruits', organic: true, stock: 50, rating: 4.7 },
  { id: 'p5', name: { fa: 'عسل آویشن', en: 'Avishan Honey' }, producer: 'Alborz Beekeepers', price: 320000, unit: '500 g', category: 'Honey', organic: false, stock: 30, rating: 4.5 },
  { id: 'p6', name: { fa: 'رب انار', en: 'Pomegranate Molasses' }, producer: 'Saveh Molasses', price: 480000, unit: '500 ml', category: 'Condiments', organic: false, stock: 0, rating: 4.2 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'جستجوی محصولات', en: 'Product Search' };
  const descriptions: Record<string, string> = { fa: 'جستجوی هوشمند با فیلترهای پیشرفته', en: 'Smart search with advanced filters' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search`, languages: { fa: `${BASE_URL}/fa/market/search`, en: `${BASE_URL}/en/market/search` } },
  };
}

export default async function SearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const loc = locale as 'fa' | 'en';
  setRequestLocale(locale);
  const t = await getTranslations('market.search');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Search Engine" label={t('provenanceLabel')} verified={true} method="Indexed" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Full-text + semantic search', 'Faceted filters', 'Multi-language']}
          limits={['Index freshness lag', 'Semantic search WIP', 'Voice search beta']}
          next={['Add vector search', 'Enable saved searches', 'Search analytics']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <Card density="cozy">
          <div className="space-y-4">
            <div className="flex gap-3">
              <input
                type="search"
                placeholder={t('searchPlaceholder')}
                className="flex-1 px-4 py-3 rounded-lg border border-line bg-surface text-ink text-lg focus:outline-none focus:ring-2 focus:ring-forest"
                autoFocus
              />
              <Button variant="primary" size="lg" className="whitespace-nowrap">{common('search')}</Button>
            </div>
            <div className="flex flex-wrap gap-3 text-sm text-ink-soft">
              <span>{t('searchTips')}</span>
              <span className="px-2 py-1 rounded bg-forest/10 text-forest">{t('organic')}</span>
              <span className="px-2 py-1 rounded bg-blue/10 text-blue">{t('waterSaving')}</span>
              <span className="px-2 py-1 rounded bg-amber/10 text-amber">{t('local')}</span>
            </div>
          </div>
        </Card>

        <div className="mt-8 grid gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-ink">{t('results')}: <span className="text-forest">6</span> {t('found')}</h2>
            <select className="px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
              <option value="rating">{common('sortByRating')}</option>
              <option value="price-asc">{common('priceLowHigh')}</option>
              <option value="price-desc">{common('priceHighLow')}</option>
            </select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {MOCK_PRODUCTS.map(p => (
              <Card key={p.id} density="compact">
                <div className="aspect-square flex items-center justify-center bg-slate/10 rounded">
                  📷
                </div>
                <h3 className="font-medium text-ink mt-2 line-clamp-1">{p.name[loc] ?? p.name.fa}</h3>
                <p className="text-sm text-ink-soft">{p.producer}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}</span>
                  <StatusDot state={p.stock > 0 ? 'ok' : 'down'} label={p.stock > 0 ? common('inStock') : common('outOfStock')} />
                </div>
                {p.organic && <span className="mt-2 inline-block text-xs bg-forest/10 text-forest px-2 py-1 rounded">{common('organic')}</span>}
                <Button variant="primary" size="sm" className="w-full mt-3" onClick={() => window.location.href = `/${locale}/market/product/${p.id}`}>{common('view')}</Button>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}