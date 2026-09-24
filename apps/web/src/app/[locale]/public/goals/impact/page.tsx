import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Stat } from '@/components/ui/Stat';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'تأثیر', en: 'Impact' };
  const descriptions: Record<string, string> = { fa: 'شاخص‌های تأثیر پلتفرم', en: 'Platform impact metrics' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/impact`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/impact`, languages: { fa: `${BASE_URL}/fa/public/goals/impact`, en: `${BASE_URL}/en/public/goals/impact` } },
  };
}

export default async function ImpactPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.impact');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Impact Measurement" label={t('provenanceLabel')} verified={true} method="M&E framework" timestamp="2024-12-10">
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
          evidence={['Baseline surveys', 'Remote sensing validation', 'Farmer income tracking']}
          limits={['Attribution complexity', 'Lagging indicators', 'Control group challenges']}
          next={['Publish impact report', 'Add counterfactual analysis', 'Link to carbon credits']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('keyIndicators')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label={t('waterSaved')} value="2.4M m³" provenance={{ source: 'Hydrology Model', verified: true, method: 'FAO-56 + Satellite', timestamp: '2024-12-01' }} />
          <Stat label={t('carbonSequestered')} value="15,200 tCO₂" provenance={{ source: 'Carbon Registry', verified: true, method: 'IPCC Tier 2 + VVB', timestamp: '2024-12-01' }} />
          <Stat label={t('soilRestored')} value="1,200 ha" provenance={{ source: 'Land Profiler', verified: true, method: 'RUSLE + Ground Truth', timestamp: '2024-12-01' }} />
          <Stat label={t('incomeIncreased')} value="27%" provenance={{ source: 'Socioeconomic Survey', verified: true, method: 'Household Survey', timestamp: '2024-12-01' }} />
        </div>
      </section>
    </main>
  );
}