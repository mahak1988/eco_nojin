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
  const titles: Record<string, string> = { fa: 'شمارش مدل‌ها', en: 'Model Count' };
  const descriptions: Record<string, string> = { fa: 'تعداد و وضعیت مدل‌های علمی ثبت‌شده', en: 'Registered scientific models count and status' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/model-count`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/model-count`, languages: { fa: `${BASE_URL}/fa/public/model-count`, en: `${BASE_URL}/en/public/model-count` } },
  };
}

export default async function ModelCountPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.modelCount');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Model Registry" label={t('provenanceLabel')} verified={true} method="Auto-counted" timestamp="2024-12-10">
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
          evidence={['62 registered models', 'Version-controlled', 'CI-validated']}
          limits={['Experimental models excluded', 'Deprecation policy WIP', 'Regional calibration gaps']}
          next={['Add model cards', 'Enable comparison', 'Publish performance benchmarks']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('modelCategories')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label={t('soilModels')} value="14" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
          <Stat label={t('waterModels')} value="18" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
          <Stat label={t('climateModels')} value="12" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
          <Stat label={t('carbonModels')} value="10" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
          <Stat label={t('erosionModels')} value="5" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
          <Stat label={t('economicModels')} value="3" provenance={{ source: 'Model Registry', verified: true, method: 'Auto', timestamp: '2024-12-10' }} />
        </div>
      </section>
    </main>
  );
}