import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Benchmark {
  id: string;
  name: string;
  dataset: string;
  variable: string;
  models: string[];
  metric: string;
  value: string;
  status: 'pass' | 'fail' | 'partial';
}

const MOCK_BENCHMARKS: Benchmark[] = [
  { id: 'b1', name: 'MOPEX Streamflow', dataset: 'MOPEX', variable: 'Daily Q', models: ['HEC-HMS', 'SAC-SMA', 'VIC'], metric: 'NSE', value: '>0.65', status: 'pass' },
  { id: 'b2', name: 'CAMELS Water Balance', dataset: 'CAMELS', variable: 'Annual Q', models: ['VIC', 'SWAT', 'HEC-HMS'], metric: 'KGE', value: '>0.55', status: 'partial' },
  { id: 'b3', name: 'FLUXNET ET', dataset: 'FLUXNET', variable: 'Daily ET', models: ['FAO-56', 'SEBAL', 'METRIC'], metric: 'RMSE', value: '<1.2 mm/d', status: 'pass' },
  { id: 'b4', name: 'SoilGrids SOC', dataset: 'SoilGrids', variable: 'SOC 0-30cm', models: ['RothC', 'Century', 'SoilCarbon'], metric: 'R²', value: '>0.60', status: 'partial' },
  { id: 'b5', name: 'GLDAS Soil Moisture', dataset: 'GLDAS', variable: 'SM 0-10cm', models: ['SWAT', 'VIC', 'HEC-HMS'], metric: 'ubRMSE', value: '<0.04 m³/m³', status: 'fail' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'معیارهای مقایسه', en: 'Benchmarks' };
  const descriptions: Record<string, string> = { fa: 'بندمارک‌های استاندارد برای ارزیابی مدل‌ها', en: 'Standard benchmarks for model evaluation' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/benchmarks`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/benchmarks`, languages: { fa: `${BASE_URL}/fa/public/science/benchmarks`, en: `${BASE_URL}/en/public/science/benchmarks` } },
  };
}

export default async function BenchmarksPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.benchmarks');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Benchmark Suite" label={t('provenanceLabel')} verified={true} method="Standard datasets" timestamp="2024-12-10">
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
          evidence={['MOPEX, CAMELS, FLUXNET', 'Standard metrics (NSE, KGE, RMSE)', 'Open leaderboard']}
          limits={['Regional representativeness', 'Metric threshold subjectivity', 'Model version drift']}
          next={['Add regional benchmarks', 'Automated CI validation', 'Publish leaderboard API']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('benchmarkTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('benchmark')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('dataset')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('variable')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('models')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('metric')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('target')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('status')}</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_BENCHMARKS.map(b => (
                <tr key={b.id} className="border-b border-line/50">
                  <td className="py-2 px-3 font-medium text-ink">{b.name}</td>
                  <td className="py-2 px-3 text-ink-soft">{b.dataset}</td>
                  <td className="py-2 px-3 text-ink-soft">{b.variable}</td>
                  <td className="py-2 px-3 text-ink-soft">{b.models.join(', ')}</td>
                  <td className="py-2 px-3 font-mono text-ink">{b.metric}</td>
                  <td className="py-2 px-3 font-mono text-ink">{b.value}</td>
                  <td className="py-2 px-3">
                    <StatusDot state={b.status === 'pass' ? 'ok' : b.status === 'partial' ? 'warn' : 'down'} label={common(b.status)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="Benchmark Suite" verified={true} method="Standard datasets" timestamp="2024-12-10" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}