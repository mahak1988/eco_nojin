import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Collection {
  id: string;
  name: string;
  description: string;
  itemCount: number;
  languages: string[];
  status: 'live' | 'beta' | 'draft';
  curator: string;
}

const MOCK_COLLECTIONS: Collection[] = [
  { id: 'col1', name: 'Regenerative Agriculture Core', description: 'Foundational principles and practices', itemCount: 42, languages: ['fa','en','ar','es','fr'], status: 'live', curator: 'FAO' },
  { id: 'col2', name: 'Water-Smart Farming', description: 'Irrigation, drainage, water productivity', itemCount: 28, languages: ['fa','en','ur','hi'], status: 'live', curator: 'ICARDA' },
  { id: 'col3', name: 'Carbon Farming Toolkit', description: 'Sequestration, verification, markets', itemCount: 35, languages: ['en','fr','es','pt'], status: 'beta', curator: 'Verra/GS' },
  { id: 'col4', name: 'Soil Health Assessment', description: 'Indicators, methods, interpretation', itemCount: 22, languages: ['fa','en','ar'], status: 'live', curator: 'ISRIC' },
  { id: 'col5', name: 'Climate-Resilient Crops', description: 'Varieties, breeding, adaptation', itemCount: 18, languages: ['fa','en','zh','ru'], status: 'draft', curator: 'CGIAR' },
  { id: 'col6', name: 'Policy & Governance', description: 'Land tenure, water rights, subsidies', itemCount: 15, languages: ['fa','en','ar','es'], status: 'beta', curator: 'World Bank' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کتابخانه پیشرفته', en: 'Advanced Library' };
  const descriptions: Record<string, string> = { fa: 'مجموعه‌های منسق محتوای آموزشی', en: 'Curated educational content collections' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/library-advanced`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/library-advanced`, languages: { fa: `${BASE_URL}/fa/public/education/library-advanced`, en: `${BASE_URL}/en/public/education/library-advanced` } },
  };
}

export default async function LibraryAdvancedPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.libraryAdvanced');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Collection Registry" label={t('provenanceLabel')} verified={true} method="Curator-verified" timestamp="2024-12-10">
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
          evidence={['6 curated collections', 'Multi-language', 'Expert curators']}
          limits={['Collection gaps', 'Translation coverage varies', 'Update frequency manual']}
          next={['Add collection builder', 'Enable annotations', 'Version tracking']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('collections')}</h2>
        <div className="grid gap-4">
          {MOCK_COLLECTIONS.map(col => (
            <Card key={col.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{col.name}</h3>
                  <p className="text-sm text-ink-soft mt-1">{col.description}</p>
                  <p className="text-xs text-ink-soft">{col.itemCount} {t('items')} · Curator: {col.curator}</p>
                  <div className="flex flex-wrap gap-1 mt-2 text-xs">
                    {col.languages.map(l => <span key={l} className="px-1.5 py-0.5 rounded bg-forest/10 text-forest">{l}</span>)}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={col.status === 'live' ? 'ok' : col.status === 'beta' ? 'warn' : 'down'} label={common(col.status)} />
                  <Button variant="ghost" size="sm">{t('browse')}</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}