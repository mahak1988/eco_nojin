import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Gap {
  id: string;
  domain: string;
  title: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  effort: 'small' | 'medium' | 'large';
  owner: string;
}

const MOCK_GAPS: Gap[] = [
  { id: 'g1', domain: 'Data', title: 'Real-time Soil Moisture Network', description: 'No in-situ SM sensors in pilot provinces', priority: 'critical', effort: 'large', owner: 'Field Monitoring' },
  { id: 'g2', domain: 'Model', title: 'Coupled Surface-Groundwater', description: 'Current models treat SW/GW separately', priority: 'high', effort: 'large', owner: 'HydroMa Core' },
  { id: 'g3', domain: 'Carbon', title: 'Belowground Carbon Dynamics', description: 'Root exudation, mycorrhizal C not represented', priority: 'high', effort: 'medium', owner: 'Carbon Team' },
  { id: 'g4', domain: 'Social', title: 'Farmer Decision Modeling', description: 'Adoption behavior not in optimization', priority: 'medium', effort: 'medium', owner: 'DSS Team' },
  { id: 'g5', domain: 'Tech', title: 'WASM Offline Compute Bundle', description: 'No browser-side model execution', priority: 'high', effort: 'medium', owner: 'Frontend' },
  { id: 'g6', domain: 'Policy', title: 'Water Rights Integration', description: 'Legal allocation not in optimization constraints', priority: 'medium', effort: 'small', owner: 'Governance' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'تحلیل شکاف', en: 'Gap Analysis' };
  const descriptions: Record<string, string> = { fa: 'شکاف‌های شناخته‌شده در داده، مدل و فرآیند', en: 'Known gaps in data, models, and processes' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/gap-analysis`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/gap-analysis`, languages: { fa: `${BASE_URL}/fa/public/science/gap-analysis`, en: `${BASE_URL}/en/public/science/gap-analysis` } },
  };
}

export default async function GapAnalysisPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.gapAnalysis');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Gap Registry" label={t('provenanceLabel')} verified={true} method="Team-identified" timestamp="2024-12-10">
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
          evidence={['6 prioritized gaps', 'Cross-team identification', 'Effort/priority matrix']}
          limits={['Subjective prioritization', 'Effort estimates rough', 'Dependencies not mapped']}
          next={['Add dependency graph', 'Link to roadmap milestones', 'Quarterly gap review']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('gaps')}</h2>
        <div className="grid gap-4">
          {MOCK_GAPS.map(g => (
            <Card key={g.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{g.title}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {g.priority === 'critical' ? 'bg-red/10 text-red' :
                       g.priority === 'high' ? 'bg-amber/10 text-amber' :
                       g.priority === 'medium' ? 'bg-blue/10 text-blue' :
                       'bg-forest/10 text-forest'}">
                      {g.priority}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{g.description}</p>
                  <p className="text-xs text-ink-soft mt-1">Domain: {g.domain} · Effort: {g.effort} · Owner: {g.owner}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={g.priority === 'critical' ? 'down' : g.priority === 'high' ? 'warn' : 'ok'} label={common(g.priority)} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}