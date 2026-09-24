import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface ValidationCheck {
  id: string;
  name: string;
  status: 'pass' | 'fail' | 'warning';
  description: string;
  lastRun: string;
}

const MOCK_VALIDATIONS: ValidationCheck[] = [
  { id: 'v1', name: 'Mass Balance Closure', status: 'pass', description: 'Water mass balance within 0.5% tolerance', lastRun: '2024-12-10' },
  { id: 'v2', name: 'Energy Balance Closure', status: 'pass', description: 'Surface energy balance within 2% tolerance', lastRun: '2024-12-10' },
  { id: 'v3', name: 'Carbon Budget Consistency', status: 'warning', description: 'Minor discrepancy in soil carbon pools', lastRun: '2024-12-08' },
  { id: 'v4', name: 'Spatial Resolution Check', status: 'pass', description: 'All rasters aligned to 10m grid', lastRun: '2024-12-10' },
  { id: 'v5', name: 'Temporal Consistency', status: 'fail', description: 'Gap in ERA5 forcing data 2024-11-15', lastRun: '2024-12-09' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'ابزارهای اعتبارسنجی', en: 'Validation Tools' };
  const descriptions: Record<string, string> = { fa: 'بررسی‌های کیفیت داده و مدل', en: 'Data and model quality checks' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/validation`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/validation`, languages: { fa: `${BASE_URL}/fa/public/science/validation`, en: `${BASE_URL}/en/public/science/validation` } },
  };
}

export default async function ValidationPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.validation');
  const common = await getTranslations('common');

  const runAll = () => alert(t('runningAll'));

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex items-center justify-between">
          <ProvenanceStamp source="Validation Engine" label={t('provenanceLabel')} verified={true} method="Automated QA/QC" timestamp="2024-12-10">
            <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
          </ProvenanceStamp>
          <Button variant="primary" onClick={runAll}>{t('runAll')}</Button>
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Automated QA/QC pipelines', 'Cross-variable consistency', 'Benchmark datasets']}
          limits={['Manual review needed for failures', 'Regional benchmarks limited', 'Real-time validation not yet live']}
          next={['Enable streaming validation', 'Add ML anomaly detection', 'Integrate with model registry']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('checksCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_VALIDATIONS.map(check => (
            <Card key={check.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{check.name}</h3>
                    <StatusDot state={check.status === 'pass' ? 'ok' : check.status === 'warning' ? 'warn' : 'down'} label={common(check.status)} />
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{check.description}</p>
                </div>
                <ProvenanceStamp source="Validation Engine" verified={check.status === 'pass'} method="Automated" timestamp={check.lastRun} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}