import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface UncertaintyItem {
  id: string;
  variable: string;
  method: string;
  range: string;
  confidence: number;
  source: string;
}

const MOCK_UNCERTAINTY: UncertaintyItem[] = [
  { id: 'u1', variable: 'Soil Organic Carbon', method: 'Monte Carlo (LHS, n=10000)', range: '±12.3 tC/ha', confidence: 95, source: 'IPCC 2006 Tier 2' },
  { id: 'u2', variable: 'Evapotranspiration', method: 'GLUE (5000 runs)', range: '±8.7%', confidence: 90, source: 'FAO-56 Validation' },
  { id: 'u3', variable: 'Soil Erosion Rate', method: 'Sobol Sensitivity', range: '±23.4%', confidence: 95, source: 'RUSLE2 Calibration' },
  { id: 'u4', variable: 'Crop Yield', method: 'Bayesian Calibration', range: '±15.2%', confidence: 85, source: 'AquaCrop-OSPy' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کمیت‌سازی عدم قطعیت', en: 'Uncertainty Quantification' };
  const descriptions: Record<string, string> = { fa: 'بازه‌های اطمینان و تحلیل حساسیت', en: 'Confidence intervals and sensitivity analysis' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/uncertainty`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/uncertainty`, languages: { fa: `${BASE_URL}/fa/public/science/uncertainty`, en: `${BASE_URL}/en/public/science/uncertainty` } },
  };
}

export default async function UncertaintyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.uncertainty');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="UQ Engine" label={t('provenanceLabel')} verified={true} method="MC/LHS/Sobol" timestamp="2024-12-10">
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
          evidence={['Monte Carlo (LHS)', 'Sobol indices', 'GLUE/Bayesian']}
          limits={['Computational cost high', 'Prior distributions subjective', 'Correlation structures simplified']}
          next={['Add polynomial chaos', 'Enable real-time UQ', 'Link to decision support']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('uqCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_UNCERTAINTY.map(item => (
            <Card key={item.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{item.variable}</h3>
                  <p className="text-sm text-ink-soft">{item.method}</p>
                  <p className="text-xs text-ink-soft">Range: {item.range} · CI: {item.confidence}%</p>
                </div>
                <ProvenanceStamp source={item.source} verified={true} method={item.method} label={item.range} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}