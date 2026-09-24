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
  const descriptions: Record<string, string> = { fa: 'سازماندهی پرس‌وجو با منطق بولی', en: 'Boolean query builder' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/advanced`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/advanced`, languages: { fa: `${BASE_URL}/fa/market/search/advanced`, en: `${BASE_URL}/en/market/search/advanced` } },
  };
}

export default async function AdvancedSearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.advanced');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-4xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Advanced Search" label={t('provenanceLabel')} verified={true} method="Boolean" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-4xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Boolean logic (AND/OR/NOT)', 'Field-specific search', 'Saved queries']}
          limits={['Learning curve', 'Performance on complex queries', 'Mobile builder UX']}
          next={['Add visual query builder', 'Enable query templates', 'Search history']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-4xl px-6 pb-12">
        <Card density="cozy">
          <div className="space-y-4">
            <div className="flex gap-2">
              <select className="px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                <option value="name">{t('productName')}</option>
                <option value="producer">{t('producer')}</option>
                <option value="category">{t('category')}</option>
                <option value="description">{t('description')}</option>
              </select>
              <select className="px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                <option value="contains">{t('contains')}</option>
                <option value="equals">{t('equals')}</option>
                <option value="startsWith">{t('startsWith')}</option>
                <option value="endsWith">{t('endsWith')}</option>
              </select>
              <input type="text" placeholder={t('value')} className="flex-1 px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest" />
              <select className="px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest">
                <option value="AND">{t('and')}</option>
                <option value="OR">{t('or')}</option>
                <option value="NOT">{t('not')}</option>
              </select>
            </div>

            <div className="border-t border-line pt-4">
              <p className="text-sm text-ink-soft mb-2">{t('queryPreview')}</p>
              <code className="block p-3 bg-slate/10 rounded text-sm font-mono text-ink">name:contains:"pistachio" AND category:equals:"nuts" AND organic:equals:true</code>
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="ghost">{t('saveQuery')}</Button>
              <Button variant="primary">{common('search')}</Button>
            </div>
          </div>
        </Card>
      </section>
    </main>
  );
}