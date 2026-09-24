import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const mockProducts: Record<string, Array<{id: string, name: {fa: string, en: string}, price: number, unit: string, producer: string, organic: boolean, stock: number, rating: number, certifications: string[]}>> = {
  'pistachios': [
    { id: 'p1', name: { fa: 'پسته ارگانیک آکبری', en: 'Organic Akbari Pistachio' }, price: 285000, unit: '1 kg', producer: 'Rafsanjan Organic Co', organic: true, stock: 18, rating: 4.9, certifications: ['Organic', 'Fair Trade'] },
    { id: 'p2', name: { fa: 'پسته ارگانیک احمد آغایی', en: 'Organic Ahmad Aghaei Pistachio' }, price: 265000, unit: '1 kg', producer: 'Kerman Eco Farm', organic: true, stock: 22, rating: 4.8, certifications: ['Organic'] },
    { id: 'p3', name: { fa: 'پسته ارگانیک اکبری سوپر', en: 'Super Organic Akbari' }, price: 320000, unit: '1 kg', producer: 'Premium Pistachio', organic: true, stock: 10, rating: 4.95, certifications: ['Organic', 'Fair Trade', 'Carbon Neutral'] },
  ],
  'almonds': [
    { id: 'p4', name: { fa: 'بادام ممان ارگانیک', en: 'Organic Maman Almonds' }, price: 195000, unit: '500 g', producer: 'Gilan Almond Co', organic: true, stock: 15, rating: 4.7, certifications: ['Organic'] },
  ],
  'saffron-super-negin': [
    { id: 'p5', name: { fa: 'زعفران سوپر نگین ارگانیک', en: 'Organic Super Negin Saffron' }, price: 8900000, unit: '5 g', producer: 'Khorasan Saffron', organic: true, stock: 8, rating: 4.9, certifications: ['Organic', 'ISO 3632'] },
  ],
};

function getCategoryInfo(level1: string, level2: string, level3: string) {
  const info: Record<string, Record<string, Record<string, {name: {fa: string, en: string}, parent: string}>>> = {
    'nuts-dried-fruits': {
      'nuts': {
        'pistachios': { name: { fa: 'پسته', en: 'Pistachios' }, parent: 'nuts' },
        'almonds': { name: { fa: 'بادام', en: 'Almonds' }, parent: 'nuts' },
      },
      'dried-fruits': {},
    },
    'spices-saffron': {
      'saffron-super-negin': {
        'saffron-super-negin': { name: { fa: 'زعفران سوپر نگین', en: 'Super Negin Saffron' }, parent: 'saffron-super-negin' },
      },
    },
  };
  return info[level1]?.[level2]?.[level3] || { name: { fa: level3, en: level3 }, parent: level2 };
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string; level1: string; level2: string; level3: string }> }): Promise<Metadata> {
  const { locale, level1, level2, level3 } = await params;
  const cat = getCategoryInfo(level1, level2, level3);
  const loc = locale as 'fa' | 'en';
  return {
    title: cat.name[loc] ?? cat.name.fa,
    description: `محصولات ${cat.name[loc] ?? cat.name.fa}`,
    openGraph: { type: 'website', locale, title: cat.name[loc] ?? cat.name.fa },
    alternates: { canonical: `${BASE_URL}/${locale}/market/categories/${level1}/${level2}/${level3}` },
  };
}

export default async function CategoryLevel3Page({ params }: { params: Promise<{ locale: string; level1: string; level2: string; level3: string }> }) {
  const { locale, level1, level2, level3 } = await params;
  const loc = locale as 'fa' | 'en';
  setRequestLocale(locale);
  const t = await getTranslations('market.categories');
  const common = await getTranslations('common');
  const cat = getCategoryInfo(level1, level2, level3);
  const catName = cat.name as Record<'fa' | 'en', string>;
  const products = mockProducts[level3] || [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <button onClick={() => window.location.href = `/${locale}/market/categories`} className="underline hover:text-ink">{common('categories')}</button>
          <span> / </span>
          <button onClick={() => window.location.href = `/${locale}/market/categories/${level1}`} className="underline hover:text-ink">{t('level1')}</button>
          <span> / </span>
          <button onClick={() => window.location.href = `/${locale}/market/categories/${level1}/${level2}`} className="underline hover:text-ink">{t('level2')}</button>
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
            <option value="organic">{t('organicFirst')}</option>
          </select>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map(p => (
            <Card key={p.id} density="compact">
              <div className="aspect-square flex items-center justify-center bg-slate/10 rounded">
                📷
              </div>
              <h3 className="font-medium text-ink mt-2 line-clamp-1">{p.name[loc] ?? p.name.fa}</h3>
              <p className="text-sm text-ink-soft">{p.producer}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {p.certifications.map(c => <span key={c} className="px-2 py-1 rounded text-xs bg-amber/10 text-amber">{c}</span>)}
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}</span>
                <StatusDot state={p.stock > 0 ? 'ok' : 'down'} label={p.stock > 0 ? common('inStock') : common('outOfStock')} />
              </div>
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