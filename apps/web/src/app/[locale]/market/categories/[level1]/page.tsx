import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const mockSubcategories: Record<string, Array<{id: string, name: {fa: string, en: string}, slug: string, productCount: number, icon: string}>> = {
  'nuts-dried-fruits': [
    { id: 'cat3', name: { fa: 'مکسرات', en: 'Nuts' }, slug: 'nuts', productCount: 18, icon: '🥜' },
    { id: 'cat4', name: { fa: 'خشکبار', en: 'Dried Fruits' }, slug: 'dried-fruits', productCount: 15, icon: '🍑' },
  ],
  'spices-saffron': [
    { id: 'cat7', name: { fa: 'زعفران سوپر نگین', en: 'Super Negin Saffron' }, slug: 'saffron-super-negin', productCount: 10, icon: '🌿' },
  ],
};

const mockProducts: Record<string, Array<{id: string, name: {fa: string, en: string}, price: number, unit: string, producer: string, organic: boolean, stock: number, rating: number}>> = {
  'nuts-dried-fruits': [
    { id: 'p1', name: { fa: 'پسته ارگانیک', en: 'Organic Pistachio' }, price: 245000, unit: '1 kg', producer: 'Kerman Coop', organic: true, stock: 42, rating: 4.8 },
    { id: 'p2', name: { fa: 'بادام maman', en: 'Maman Almonds' }, price: 185000, unit: '500 g', producer: 'Gilan Co-op', organic: true, stock: 25, rating: 4.6 },
  ],
};

function getCategoryName(slug: string, locale: string) {
  const names: Record<string, {fa: string, en: string}> = {
    'nuts-dried-fruits': { fa: 'آجیل و خشکبار', en: 'Nuts & Dried Fruits' },
    'spices-saffron': { fa: 'ادویه و زعفران', en: 'Spices & Saffron' },
  };
  const loc = locale as 'fa' | 'en';
  return names[slug]?.[loc] ?? names[slug]?.fa ?? slug;
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string; level1: string }> }): Promise<Metadata> {
  const { locale, level1 } = await params;
  const catName = getCategoryName(level1, locale);
  const titles: Record<string, string> = { fa: catName, en: catName };
  return {
    title: catName,
    description: `محصولات دسته ${catName}`,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/categories/${level1}`, title: catName },
    alternates: { canonical: `${BASE_URL}/${locale}/market/categories/${level1}`, languages: { fa: `${BASE_URL}/fa/market/categories/${level1}`, en: `${BASE_URL}/en/market/categories/${level1}` } },
  };
}

export default async function CategoryLevel1Page({ params }: { params: Promise<{ locale: string; level1: string }> }) {
  const { locale, level1 } = await params;
  const loc = locale as 'fa' | 'en';
  setRequestLocale(locale);
  const t = await getTranslations('market.categories');
  const common = await getTranslations('common');
  const catName = getCategoryName(level1, loc);
  const subcats = mockSubcategories[level1] || [];
  const products = mockProducts[level1] || [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <button onClick={() => window.location.href = `/${locale}/market/categories`} className="underline hover:text-ink">{common('categories')}</button>
          <span> / </span>
          <span className="text-ink">{catName}</span>
        </nav>
        <ProvenanceStamp source="Category Registry" label={t('provenanceLabel')} verified={true} method="Taxonomy-managed" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{catName}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Subcategories', 'Product listings', 'Semantic filters']}
          limits={['Regional availability varies', 'Stock real-time sync WIP']}
          next={['Add comparison', 'Enable subscriptions', 'Price alerts']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        {subcats.length > 0 && (
          <>
            <h2 className="text-xl font-semibold text-ink mb-4">{t('subcategories')}</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-8">
              {subcats.map(sub => {
                const subName = sub.name as Record<string, string>;
                return (
                  <Card key={sub.id} density="cozy">
                    <div className="flex items-start gap-4">
                      <span className="text-3xl">{sub.icon}</span>
                      <div className="flex-1">
                        <h3 className="font-semibold text-ink">{subName[loc] ?? subName.fa}</h3>
                        <p className="text-sm text-ink-soft mt-1">{sub.productCount} {t('products')}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => window.location.href = `/${locale}/market/categories/${level1}/${sub.slug}`}>
                        {common('browse')}
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>
          </>
        )}

        <h2 className="text-xl font-semibold text-ink mb-4">{t('featuredProducts')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map(p => {
                const pName = p.name as Record<string, string>;
                return (
                  <Card key={p.id} density="compact">
                    <div className="aspect-square flex items-center justify-center bg-slate/10 rounded">
                      📷
                    </div>
                    <h3 className="font-medium text-ink mt-2">{pName[loc] ?? pName.fa}</h3>
                    <p className="text-sm text-ink-soft">{p.producer}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}</span>
                      <StatusDot state={p.stock > 0 ? 'ok' : 'down'} label={p.stock > 0 ? common('inStock') : common('outOfStock')} />
                    </div>
                    {p.organic && <span className="mt-2 inline-block text-xs bg-forest/10 text-forest px-2 py-1 rounded">{common('organic')}</span>}
                    <Button variant="primary" size="sm" className="w-full mt-3">{common('view')}</Button>
                  </Card>
                );
              })}
        </div>
      </section>
    </main>
  );
}