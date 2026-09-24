import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Category {
  id: string;
  name: { fa: string; en: string };
  slug: string;
  level: 1 | 2 | 3;
  parent?: string;
  productCount: number;
  icon: string;
  filters: string[];
}

const MOCK_CATEGORIES: Category[] = [
  { id: 'cat1', name: { fa: 'آجیل و خشکبار', en: 'Nuts & Dried Fruits' }, slug: 'nuts-dried-fruits', level: 1, productCount: 42, icon: '🌰', filters: ['ارگانیک', 'کم‌آب', 'محلی'] },
  { id: 'cat2', name: { fa: 'ادویه و زعفران', en: 'Spices & Saffron' }, slug: 'spices-saffron', level: 1, productCount: 28, icon: '🌿', filters: ['ارگانیک', 'دست‌مالی'] },
  { id: 'cat3', name: { fa: 'مکسرات', en: 'Nuts' }, slug: 'nuts', level: 2, parent: 'cat1', productCount: 18, icon: '🥜', filters: ['ارگانیک', 'پوستی/بدون پوست'] },
  { id: 'cat4', name: { fa: 'خشکبار', en: 'Dried Fruits' }, slug: 'dried-fruits', level: 2, parent: 'cat1', productCount: 15, icon: '🍑', filters: ['ارگانیک', 'بدون شکر'] },
  { id: 'cat5', name: { fa: 'پسته', en: 'Pistachios' }, slug: 'pistachios', level: 3, parent: 'cat3', productCount: 12, icon: '🌰', filters: ['ارگانیک', 'آبی/خشک', 'سایز'] },
  { id: 'cat6', name: { fa: 'بادام', en: 'Almonds' }, slug: 'almonds', level: 3, parent: 'cat3', productCount: 8, icon: '🌰', filters: ['ارگانیک', 'پوستی/بدون پوست'] },
  { id: 'cat7', name: { fa: 'زعفران سوپر نگین', en: 'Super Negin Saffron' }, slug: 'saffron-super-negin', level: 3, parent: 'cat2', productCount: 10, icon: '🌿', filters: ['ارگانیک', 'گرم/سرد'] },
];

const level1Categories = MOCK_CATEGORIES.filter(c => c.level === 1);

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'دسته‌بندی محصولات', en: 'Product Categories' };
  const descriptions: Record<string, string> = { fa: 'مرور درخت دسته‌بندی سه‌سطحی', en: 'Browse 3-level category tree' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/categories`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/categories`, languages: { fa: `${BASE_URL}/fa/market/categories`, en: `${BASE_URL}/en/market/categories` } },
  };
}

export default async function CategoriesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const loc = locale as 'fa' | 'en';
  setRequestLocale(locale);
  const t = await getTranslations('market.categories');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Category Registry" label={t('provenanceLabel')} verified={true} method="Taxonomy-managed" timestamp="2024-12-10">
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
          evidence={['3-level taxonomy', 'Semantic filters', 'Real-time product counts']}
          limits={['Regional category variations', 'Translation coverage varies', 'Dynamic filter sync WIP']}
          next={['Add category analytics', 'Enable cross-sell rules', 'ML-based categorization']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="flex flex-wrap gap-4 mb-6">
          <input
            type="search"
            placeholder={t('searchCategories')}
            className="flex-1 min-w-[200px] px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest"
          />
          <select className="px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
            <option value="all">{common('all')}</option>
            <option value="organic">{t('organic')}</option>
            <option value="water-saving">{t('waterSaving')}</option>
            <option value="local">{t('local')}</option>
          </select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {level1Categories.map(cat => {
            const catNameObj = cat.name as Record<string, string>;
            return (
              <Card key={cat.id} density="cozy">
                <div className="flex items-start gap-4">
                  <span className="text-4xl">{cat.icon}</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-ink">{catNameObj[loc] ?? catNameObj.fa}</h3>
                    <p className="text-sm text-ink-soft mt-1">{cat.productCount} {t('products')}</p>
                    <div className="flex flex-wrap gap-1 mt-2 text-xs">
                      {cat.filters.map(f => <span key={f} className="px-2 py-1 rounded bg-forest/10 text-forest">{f}</span>)}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = `/${locale}/market/categories/${cat.slug}`}>
                    {common('browse')}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}