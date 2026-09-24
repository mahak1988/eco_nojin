import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface LibraryItem {
  id: string;
  title: string;
  type: 'article' | 'video' | 'guide' | 'case-study';
  languages: string[];
  level: 'beginner' | 'intermediate' | 'advanced';
  source: string;
  verified: boolean;
}

const MOCK_LIBRARY: LibraryItem[] = [
  { id: 'l1', title: 'Regenerative Agriculture Principles', type: 'guide', languages: ['fa', 'en', 'ar', 'es'], level: 'beginner', source: 'FAO', verified: true },
  { id: 'l2', title: 'Soil Health Assessment Methods', type: 'article', languages: ['fa', 'en'], level: 'intermediate', source: 'ISRIC', verified: true },
  { id: 'l3', title: 'Water-Efficient Irrigation Design', type: 'video', languages: ['fa', 'en', 'ur'], level: 'beginner', source: 'ICARDA', verified: true },
  { id: 'l4', title: 'Carbon Farming Case Studies', type: 'case-study', languages: ['en', 'fr', 'pt'], level: 'advanced', source: '4 per 1000 Initiative', verified: false },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کتابخانه آموزشی', en: 'Education Library' };
  const descriptions: Record<string, string> = { fa: 'مجموعه راهنماها، ویدئوها و مقالات', en: 'Guides, videos, and articles collection' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/library`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/library`, languages: { fa: `${BASE_URL}/fa/public/education/library`, en: `${BASE_URL}/en/public/education/library` } },
  };
}

export default async function LibraryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.library');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex items-center justify-between">
          <ProvenanceStamp source="Content Registry" label={t('provenanceLabel')} verified={true} method="Curated" timestamp="2024-12-10">
            <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
          </ProvenanceStamp>
          <Button variant="primary">{t('addContent')}</Button>
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Multi-language content', 'Level-tagged resources', 'FAO/ICARDA/ISRIC sources']}
          limits={['Translation gaps for 12 locales', 'Video subtitles incomplete', 'Advanced content limited']}
          next={['Add AI translation pipeline', 'Enable community contributions', 'Link to certification tracks']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('catalog')}</h2>
        <div className="grid gap-4">
          {MOCK_LIBRARY.map(item => (
            <Card key={item.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{item.title}</h3>
                    <span className="text-xs px-2 py-1 rounded bg-forest/10 text-forest">{item.type}</span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">Level: {item.level} · Languages: {item.languages.join(', ')}</p>
                </div>
                <ProvenanceStamp source={item.source} verified={item.verified} label={item.type} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}