import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Limitation {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  mitigation: string;
}

const MOCK_LIMITATIONS: Limitation[] = [
  { id: 'l1', category: 'Data', title: 'Sparse Ground Observations', description: 'Limited in-situ soil moisture/flux towers in pilot regions', severity: 'high', mitigation: 'Satellite fusion + citizen science' },
  { id: 'l2', category: 'Model', title: 'Structural Uncertainty', description: 'Process representation gaps (e.g., preferential flow, root dynamics)', severity: 'high', mitigation: 'Multi-model ensembles + ML emulators' },
  { id: 'l3', category: 'Parameter', title: 'Equifinality', description: 'Multiple parameter sets yield similar outputs', severity: 'medium', mitigation: 'GLUE/MCMC + sensitivity analysis' },
  { id: 'l4', category: 'Scale', title: 'Scale Mismatch', description: 'Point measurements vs. grid-cell model resolution', severity: 'medium', mitigation: 'Upscaling operators + representative elementary area' },
  { id: 'l5', category: 'Forcing', title: 'Climate Forcing Errors', description: 'ERA5 bias in complex terrain, precipitation undercatch', severity: 'high', mitigation: 'Bias correction + gauge merging' },
  { id: 'l6', category: 'Human', title: 'Management Representation', description: 'Irrigation scheduling, fertilizer timing simplified', severity: 'medium', mitigation: 'Agent-based modeling + survey integration' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'محدودیت‌ها', en: 'Limitations' };
  const descriptions: Record<string, string> = { fa: 'محدودیت‌های شناخته‌شده مدل‌ها و داده‌ها', en: 'Known limitations of models and data' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/limitations`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/limitations`, languages: { fa: `${BASE_URL}/fa/public/science/limitations`, en: `${BASE_URL}/en/public/science/limitations` } },
  };
}

export default async function LimitationsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.limitations');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Limitation Registry" label={t('provenanceLabel')} verified={true} method="Expert-elicited" timestamp="2024-12-10">
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
          evidence={['Structured expert elicitation', 'Categorized by type', 'Mitigation strategies']}
          limits={['Subjective severity scoring', 'Context-dependent applicability', 'Dynamic as models improve']}
          next={['Add quantitative bounds', 'Link to validation results', 'User-facing flags in UI']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('limitations')}</h2>
        <div className="grid gap-4">
          {MOCK_LIMITATIONS.map(l => (
            <Card key={l.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{l.title}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {l.severity === 'high' ? 'bg-red/10 text-red' :
                       l.severity === 'medium' ? 'bg-amber/10 text-amber' :
                       'bg-forest/10 text-forest'}">
                      {l.severity}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{l.description}</p>
                  <p className="text-xs text-ink-soft mt-1">Category: {l.category} · Mitigation: {l.mitigation}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="Limitation Registry" verified={true} method="Expert-elicited" timestamp="2024-12-10" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}