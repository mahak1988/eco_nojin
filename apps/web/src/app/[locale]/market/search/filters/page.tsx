import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'فیلترهای پیشرفته', en: 'Advanced Filters' };
  const descriptions: Record<string, string> = { fa: 'پنل فیلترهای چندمعیاره', en: 'Multi-criteria filter panel' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/filters`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/filters`, languages: { fa: `${BASE_URL}/fa/market/search/filters`, en: `${BASE_URL}/en/market/search/filters` } },
  };
}

export default async function FiltersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.filters');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Filter Engine" label={t('provenanceLabel')} verified={true} method="Faceted" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Faceted navigation', 'Real-time counts', 'URL-shareable']}
          limits={['Performance at scale', 'Mobile UX', 'Filter dependency logic']}
          next={['Add price range slider', 'Enable filter presets', 'Analytics on filter usage']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-ink mb-3">{t('category')}</h3>
              <div className="flex flex-wrap gap-2">
                {['Nuts', 'Spices', 'Dried Fruits', 'Honey', 'Oils', 'Condiments'].map(c => (
                  <label key={c} className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                    <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                    <span className="text-sm text-ink">{c}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-6">
              <h3 className="font-semibold text-ink mb-3">{t('certifications')}</h3>
              <div className="flex flex-wrap gap-2">
                {['Organic', 'Fair Trade', 'Carbon Neutral', 'ISO 22000'].map(c => (
                  <label key={c} className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                    <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                    <span className="text-sm text-ink">{c}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="border-t border-line pt-6">
              <h3 className="font-semibold text-ink mb-3">{t('priceRange')}</h3>
              <div className="flex items-center gap-3">
                <input type="number" placeholder={t('minPrice')} className="w-32 px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
                <span className="text-ink-soft">—</span>
                <input type="number" placeholder={t('maxPrice')} className="w-32 px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
                <span className="text-ink-soft">ریال</span>
              </div>
            </div>

            <div className="border-t border-line pt-6">
              <h3 className="font-semibold text-ink mb-3">{t('attributes')}</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                  <span className="text-sm text-ink">{t('organic')}</span>
                </label>
                <label className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                  <span className="text-sm text-ink">{t('waterSaving')}</span>
                </label>
                <label className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                  <span className="text-sm text-ink">{t('local')}</span>
                </label>
                <label className="flex items-center gap-2 px-3 py-2 rounded border border-line bg-surface hover:bg-forest/5 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-forest focus:ring-forest" />
                  <span className="text-sm text-ink">{t('inStockOnly')}</span>
                </label>
              </div>
            </div>

            <div className="border-t border-line pt-6 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => {}}>{common('clearAll')}</Button>
              <Button variant="primary" onClick={() => {}}>{common('apply')}</Button>
            </div>
          </div>
        </Card>
      </section>
    </main>
  );
}