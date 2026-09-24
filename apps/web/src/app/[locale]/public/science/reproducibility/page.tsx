import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface ReproRun {
  id: string;
  model: string;
  version: string;
  inputsHash: string;
  outputsHash: string;
  status: 'match' | 'mismatch' | 'running';
  timestamp: string;
}

const MOCK_RUNS: ReproRun[] = [
  { id: 'r1', model: 'FAO-56 ET', version: '1.0', inputsHash: 'sha256:a1b2...', outputsHash: 'sha256:c3d4...', status: 'match', timestamp: '2024-12-10' },
  { id: 'r2', model: 'RUSLE2', version: '2.0', inputsHash: 'sha256:e5f6...', outputsHash: 'sha256:g7h8...', status: 'match', timestamp: '2024-12-09' },
  { id: 'r3', model: 'AquaCrop-OSPy', version: '1.0', inputsHash: 'sha256:i9j0...', outputsHash: 'sha256:k1l2...', status: 'mismatch', timestamp: '2024-12-08' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'بازتولیدپذیری', en: 'Reproducibility' };
  const descriptions: Record<string, string> = { fa: 'داشبورد بازتولید نتایج مدل', en: 'Model results reproduction dashboard' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/reproducibility`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/reproducibility`, languages: { fa: `${BASE_URL}/fa/public/science/reproducibility`, en: `${BASE_URL}/en/public/science/reproducibility` } },
  };
}

export default async function ReproducibilityPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.reproducibility');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex items-center justify-between">
          <ProvenanceStamp source="Reproducibility Engine" label={t('provenanceLabel')} verified={true} method="Hash-verified" timestamp="2024-12-10">
            <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
          </ProvenanceStamp>
          <Button variant="primary">{t('reRunAll')}</Button>
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Input/output hashing', 'Containerized environments', 'Version-pinned dependencies']}
          limits={['Non-deterministic parallel code', 'Floating-point drift', 'External API dependencies']}
          next={['Add WebAssembly reproducibility', 'Enable diff visualization', 'CI integration for all models']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('runsCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_RUNS.map(run => (
            <Card key={run.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{run.model} v{run.version}</h3>
                  <p className="text-sm text-ink-soft font-mono">In: {run.inputsHash} → Out: {run.outputsHash}</p>
                </div>
                <ProvenanceStamp source="Repro Engine" verified={run.status === 'match'} method="SHA-256" timestamp={run.timestamp} label={common(run.status)} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}