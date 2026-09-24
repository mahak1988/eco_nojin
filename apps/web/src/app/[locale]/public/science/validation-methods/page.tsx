import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface ValidationMethod {
  id: string;
  name: string;
  type: 'statistical' | 'field' | 'remote' | 'benchmark';
  description: string;
  models: string[];
  status: 'standard' | 'developing' | 'experimental';
}

const MOCK_METHODS: ValidationMethod[] = [
  { id: 'vm1', name: 'Split-sample Calibration/Validation', type: 'statistical', description: '70/30 temporal split with KGE/NSE metrics', models: ['FAO-56', 'SWAT', 'HEC-HMS'], status: 'standard' },
  { id: 'vm2', name: 'GLUE Uncertainty Analysis', type: 'statistical', description: 'Generalized Likelihood Uncertainty Estimation', models: ['SWAT', 'HEC-RAS', 'MODFLOW'], status: 'standard' },
  { id: 'vm3', name: 'Remote Sensing Validation', type: 'remote', description: 'Sentinel-2/3, Landsat, MODIS comparison', models: ['FAO-56 ET', 'SEBAL', 'METRIC'], status: 'standard' },
  { id: 'vm4', name: 'Field Plot Comparison', type: 'field', description: 'Paired plot measurements (n=127)', models: ['RUSLE2', 'WEPP', 'SoilCarbon'], status: 'standard' },
  { id: 'vm5', name: 'Benchmark Dataset Testing', type: 'benchmark', description: 'Standard test cases (MOPEX, CAMELS)', models: ['HEC-HMS', 'SAC-SMA', 'VIC'], status: 'developing' },
  { id: 'vm6', name: 'ML Emulator Cross-validation', type: 'statistical', description: 'Surrogate model validation', models: ['All (experimental)'], status: 'experimental' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'روش‌های اعتبارسنجی', en: 'Validation Methods' };
  const descriptions: Record<string, string> = { fa: 'روش‌های اعتبارسنجی مدل‌های علمی', en: 'Scientific model validation methodologies' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/validation-methods`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/validation-methods`, languages: { fa: `${BASE_URL}/fa/public/science/validation-methods`, en: `${BASE_URL}/en/public/science/validation-methods` } },
  };
}

export default async function ValidationMethodsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.validationMethods');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Validation Framework" label={t('provenanceLabel')} verified={true} method="Methodology-documented" timestamp="2024-12-10">
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
          evidence={['6 validation approaches', 'Published benchmarks', 'Reproducible code']}
          limits={['Experimental methods unproven', 'Benchmark coverage incomplete', 'Computational cost high']}
          next={['Add ML emulator validation', 'Publish validation suite', 'Community benchmark']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('methods')}</h2>
        <div className="grid gap-4">
          {MOCK_METHODS.map(m => (
            <Card key={m.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{m.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {m.status === 'standard' ? 'bg-forest/10 text-forest' :
                       m.status === 'developing' ? 'bg-amber/10 text-amber' :
                       'bg-purple/10 text-purple'}">
                      {m.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{m.description}</p>
                  <p className="text-xs text-ink-soft">Models: {m.models.join(', ')}</p>
                </div>
                <StatusDot state={m.status === 'standard' ? 'ok' : m.status === 'developing' ? 'warn' : 'down'} label={common(m.status)} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}