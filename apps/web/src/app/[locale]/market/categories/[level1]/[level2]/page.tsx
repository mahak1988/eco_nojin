import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const mockProducts: Record<string, Array<{id: string, name: {fa: string, en: string}, price: number, unit: string, producer: string, organic: boolean, stock: number, rating: number, image: string}>> = {
  'nuts': [
    { id: 'p1', name: { fa: 'پسته ارگانیک کرمان', en: 'Organic Kerman Pistachio' }, price: 245000, unit: '1 kg', producer: 'Kerman Coop', organic: true, stock: 42, rating: 4.8, image: '/pistachio.jpg' },
    { id: 'p2', name: { fa: 'پسته آکبری', en: 'Akbari Pistachio' }, price: 285000, unit: '1 kg', producer: 'Rafsanjan Co-op', organic: true, stock: 18, rating: 4.9, image: '/pistachio2.jpg' },
    { id: 'p3', name: { fa: 'بادام ممان', en: 'Maman Almonds' }, price: 185000, unit: '500 g', producer: 'Gilan Co-op', organic: true, stock: 25, rating: 4.6, image: '/almond.jpg' },
    { id: 'p4', name: { fa: 'گردو چوبی', en: 'Chobi Walnuts' }, price: 165000, unit: '500 g', producer: 'Hamedan Farm', organic: false, stock: 33, rating: 4.4, image: '/walnut.jpg' },
  ],
  'dried-fruits': [
    { id: 'p5', name: { fa: 'خرما مضافتی', en: 'Mazafati Dates' }, price: 125000, unit: '1 kg', producer: 'Bam Dates Co', organic: true, stock: 50, rating: 4.7, image: '/dates.jpg' },
    { id: 'p6', name: { fa: 'زردآلو خشک ارگانیک', en: 'Organic Dried Apricots' }, price: 95000, unit: '500 g', producer: 'Kashan Fruits', organic: true, stock: 40, rating: 4.5, image: '/apricot.jpg' },
  ],
};

function getCategoryInfo(level1: string, level2: string) {
  const info: Record<string, Record<string, {name: {fa: string, en: string}, parent: string}>> = {
    'nuts-dried-fruits': {
      'nuts': { name: { fa: 'مکسرات', en: 'Nuts' }, parent: 'nuts-dried-fruits' },
      'dried-fruits': { name: { fa: 'خشکبار', en: 'Dried Fruits' }, parent: 'nuts-dried-fruits' },
    },
  };
  return info[level1]?.[level2] || { name: { fa: level2, en: level2 }, parent: level1 };
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string; level1: string; level2: string }> }): Promise<Metadata> {
  const { locale, level1, level2 } = await params;
  const cat = getCategoryInfo(level1, level2) as { name: Record<string, string>; parent: string };
  const loc = locale as 'fa' | 'en';
  return {
    title: cat.name[loc] ?? cat.name.fa,
    description: `محصولات ${cat.name[loc] ?? cat.name.fa}`,
    openGraph: { type: 'website', locale, title: cat.name[loc] ?? cat.name.fa },
    alternates: { canonical: `${BASE_URL}/${locale}/market/categories/${level1}/${level2}` },
  };
}

export default async function CategoryLevel2Page({ params }: { params: Promise<{ locale: string; level1: string; level2: string }> }) {
  const { locale, level1, level2 } = await params;
  const loc = locale as 'fa' | 'en';
  setRequestLocale(locale);
  const t = await getTranslations('market.categories');
  const common = await getTranslations('common');
  const cat = getCategoryInfo(level1, level2) as { name: Record<string, string>; parent: string };
  const catName = cat.name as Record<'fa' | 'en', string>;
  const products = mockProducts[level2] || [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <button onClick={() => window.location.href = `/${locale}/market/categories`} className="underline hover:text-ink">{common('categories')}</button>
          <span> / </span>
          <button onClick={() => window.location.href = `/${locale}/market/categories/${level1}`} className="underline hover:text-ink">{t('backToParent')}</button>
          <span> / </span>
          <span className="text-ink">{catName[loc] ?? catName.fa}</span>
        </nav>
        <ProvenanceStamp source="Category Registry" label={t('provenanceLabel')} verified={true} method="Taxonomy-managed" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{catName[loc] ?? catName.fa}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="flex flex-wrap gap-4 mb-6">
          <input type="search" placeholder={t('searchProducts')} className="flex-1 min-w-[200px] px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
          <select className="px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
            <option value="rating">{common('sortByRating')}</option>
            <option value="price-asc">{common('priceLowHigh')}</option>
            <option value="price-desc">{common('priceHighLow')}</option>
            <option value="newest">{common('newest')}</option>
          </select>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map(p => (
            <Card key={p.id} density="compact">
              <div className="aspect-square flex items-center justify-center bg-slate/10 rounded overflow-hidden">
                <span className="text-4xl">{p.image}</span>
              </div>
              <h3 className="font-medium text-ink mt-2 line-clamp-1">{p.name[loc] ?? p.name.fa}</h3>
              <p className="text-sm text-ink-soft">{p.producer}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}</span>
                <StatusDot state={p.stock > 0 ? 'ok' : 'down'} label={p.stock > 0 ? common('inStock') : common('outOfStock')} />
              </div>
              {p.organic && <span className="mt-2 inline-block text-xs bg-forest/10 text-forest px-2 py-1 rounded">{common('organic')}</span>}
              <div className="mt-3 flex gap-2">
                <Button variant="primary" size="sm" className="flex-1" onClick={() => window.location.href = `/${locale}/market/product/${p.id}`}>{common('view')}</Button>
                <Button variant="ghost" size="sm">{common('compare')}</Button>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}