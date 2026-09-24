import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface MethodItem {
  id: string;
  name: string;
  standard: string;
  domain: string;
  verified: boolean;
  version: string;
}

const MOCK_METHODS: MethodItem[] = [
  { id: 'm1', name: 'FAO-56 Evapotranspiration', standard: 'FAO Irrigation and Drainage Paper 56', domain: 'Hydrology', verified: true, version: '1.0' },
  { id: 'm2', name: 'RUSLE2 Erosion', standard: 'USDA Agriculture Handbook 703', domain: 'Soil Conservation', verified: true, version: '2.0' },
  { id: 'm3', name: 'IPCC 2006 Guidelines', standard: 'IPCC Guidelines for National GHG Inventories', domain: 'Carbon Accounting', verified: true, version: '2006' },
  { id: 'm4', name: 'AquaCrop-OSPy', standard: 'FAO AquaCrop Model', domain: 'Crop Water Productivity', verified: false, version: '1.0' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'روش‌شناسی', en: 'Methodology' };
  const descriptions: Record<string, string> = { fa: 'استانداردها و روش‌های محاسبه علمی', en: 'Standards and scientific computation methods' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/methodology`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/methodology`, languages: { fa: `${BASE_URL}/fa/public/science/methodology`, en: `${BASE_URL}/en/public/science/methodology` } },
  };
}

export default async function MethodologyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.methodology');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Methodology Registry" label={t('provenanceLabel')} verified={true} method="Standard-indexed" timestamp="2024-12-01">
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
          evidence={['FAO standards', 'IPCC guidelines', 'OGC specifications']}
          limits={['Some methods uncalibrated for region', 'Version drift possible', 'Translation coverage varies']}
          next={['Add calibration dashboards', 'Link to model versions', 'Automate compliance checks']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('methodsCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_METHODS.map(item => (
            <Card key={item.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{item.name}</h3>
                  <p className="text-sm text-ink-soft">{item.standard}</p>
                  <p className="text-xs text-ink-soft">Domain: {item.domain} · v{item.version}</p>
                </div>
                <ProvenanceStamp source={item.standard} verified={item.verified} label={item.domain} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}