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
  const titles: Record<string, string> = { fa: 'جستجوی پیشرفته', en: 'Advanced Search' };
  const descriptions: Record<string, string> = { fa: 'جستجوی چندمعیاره در کتابخانه آموزشی', en: 'Multi-criteria search in education library' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/advanced-search`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/advanced-search`, languages: { fa: `${BASE_URL}/fa/public/education/advanced-search`, en: `${BASE_URL}/en/public/education/advanced-search` } },
  };
}

export default async function AdvancedSearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.advancedSearch');
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
          evidence={['Full-text search', 'Faceted filters', 'Multi-language']}
          limits={['Index freshness lag', 'OCR quality varies', 'Semantic search WIP']}
          next={['Add vector search', 'Enable saved searches', 'Search analytics']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('searchForm')}</h2>
        <Card density="cozy">
          <form className="space-y-4">
            <div>
              <label className="block text-sm text-ink-soft mb-1">{t('query')}</label>
              <input type="text" className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" placeholder={t('queryPlaceholder')} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('type')}</label>
                <select className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                  <option value="all">{common('all')}</option>
                  <option value="article">{t('article')}</option>
                  <option value="video">{t('video')}</option>
                  <option value="guide">{t('guide')}</option>
                  <option value="case-study">{t('caseStudy')}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('level')}</label>
                <select className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                  <option value="all">{common('all')}</option>
                  <option value="beginner">{t('beginner')}</option>
                  <option value="intermediate">{t('intermediate')}</option>
                  <option value="advanced">{t('advanced')}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('language')}</label>
                <select className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                  <option value="all">{common('all')}</option>
                  <option value="fa">فارسی</option>
                  <option value="en">English</option>
                  <option value="ar">العربية</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="ur">اردو</option>
                  <option value="hi">हिन्दी</option>
                  <option value="zh">中文</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-ink-soft mb-1">{t('source')}</label>
                <select className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                  <option value="all">{common('all')}</option>
                  <option value="fao">FAO</option>
                  <option value="icarida">ICARDA</option>
                  <option value="isric">ISRIC</option>
                  <option value="verra">Verra/GS</option>
                  <option value="hydro">HydroMa</option>
                </select>
              </div>
            </div>
            <Button variant="primary" type="submit">{t('search')}</Button>
          </form>
        </Card>
      </section>
    </main>
  );
}