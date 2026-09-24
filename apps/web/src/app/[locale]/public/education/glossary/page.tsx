import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface GlossaryTerm {
  id: string;
  term: { fa: string; en: string };
  definition: { fa: string; en: string };
  domain: string;
  source: string;
  verified: boolean;
}

const MOCK_TERMS: GlossaryTerm[] = [
  { id: 'g1', term: { fa: 'اکوترانسپیراسیون', en: 'Evapotranspiration' }, definition: { fa: 'ترکیب تبخیر از خاک و ترشح از گیاهان', en: 'Combined evaporation from soil and transpiration from plants' }, domain: 'Hydrology', source: 'FAO-56', verified: true },
  { id: 'g2', term: { fa: 'کربن آلی خاک', en: 'Soil Organic Carbon' }, definition: { fa: 'جزء کربنی متراکم از مواد آلی تجزیه‌شده در خاک', en: 'Carbon component of decomposed organic matter in soil' }, domain: 'Soil Science', source: 'IPCC 2006', verified: true },
  { id: 'g3', term: { fa: 'فرسایشographical', en: 'Soil Erosion' }, definition: { fa: 'برداشت و انتقال partículas خاک توسط آب یا باد', en: 'Detachment and transport of soil particles by water or wind' }, domain: 'Geomorphology', source: 'RUSLE', verified: true },
  { id: 'g4', term: { fa: 'سناریوی بهینه‌سازی', en: 'Optimization Scenario' }, definition: { fa: 'مجموعه پارامترها برای ماکزیمم‌سازی عملکرد سیستم', en: 'Parameter set maximizing system performance objectives' }, domain: 'Decision Support', source: 'HydroMa DSS', verified: false },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'واژه‌نامه دوزبانه', en: 'Bilingual Glossary' };
  const descriptions: Record<string, string> = { fa: 'واژه‌نامه تخصصی قابل جستجو', en: 'Searchable bilingual technical glossary' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/glossary`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/glossary`, languages: { fa: `${BASE_URL}/fa/public/education/glossary`, en: `${BASE_URL}/en/public/education/glossary` } },
  };
}

export default async function GlossaryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.glossary');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Glossary Registry" label={t('provenanceLabel')} verified={true} method="Expert-curated" timestamp="2024-12-10">
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
          evidence={['Bilingual definitions', 'Domain-tagged terms', 'Source-attributed']}
          limits={['12 more locales pending', 'Audio pronunciation missing', 'Cross-references incomplete']}
          next={['Add TTS pronunciation', 'Enable community suggestions', 'Link to model parameters']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('termsCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_TERMS.map(term => (
            <Card key={term.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{term.term[locale as 'fa' | 'en'] ?? term.term.fa}</h3>
                  <p className="text-sm text-ink-soft mt-1">{term.definition[locale as 'fa' | 'en'] ?? term.definition.fa}</p>
                  <p className="text-xs text-ink-soft">Domain: {term.domain}</p>
                </div>
                <ProvenanceStamp source={term.source} verified={term.verified} label={term.domain} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}