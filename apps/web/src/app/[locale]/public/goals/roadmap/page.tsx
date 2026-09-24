import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Milestone {
  id: string;
  quarter: string;
  title: string;
  description: string;
  status: 'completed' | 'in-progress' | 'planned';
  dependencies: string[];
}

const MOCK_MILESTONES: Milestone[] = [
  { id: 'm1', quarter: 'Q1 2025', title: 'Phase 0: Technical Foundation', description: 'Next.js + i18n + Design System + CI', status: 'completed', dependencies: [] },
  { id: 'm2', quarter: 'Q2 2025', title: 'Phase 1: Public Pages (70)', description: 'AI, Trust, Dev, Science, Education, Policy', status: 'in-progress', dependencies: ['m1'] },
  { id: 'm3', quarter: 'Q3 2025', title: 'Phase 2: Marketplace Core (182)', description: 'Catalog, Cart, Checkout, Wallet, Escrow', status: 'planned', dependencies: ['m2'] },
  { id: 'm4', quarter: 'Q4 2025', title: 'Phase 3: Institutional Bazaar (80)', description: '42 Bazaars + 38 Stores + 5-party signatures', status: 'planned', dependencies: ['m3'] },
  { id: 'm5', quarter: 'Q1 2026', title: 'Phase 4: Seller Support (115)', description: 'Warehouse, Finance, Support, Supervision', status: 'planned', dependencies: ['m3'] },
  { id: 'm6', quarter: 'Q2 2026', title: 'Phase 6: Science (174)', description: '62 Tools T07 + Model Library + Reproducibility', status: 'planned', dependencies: ['m1'] },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'نقشه راه', en: 'Roadmap' };
  const descriptions: Record<string, string> = { fa: 'نقشه راه توسعه پلتفرم', en: 'Platform development roadmap' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/roadmap`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/roadmap`, languages: { fa: `${BASE_URL}/fa/public/goals/roadmap`, en: `${BASE_URL}/en/public/goals/roadmap` } },
  };
}

export default async function RoadmapPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.roadmap');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Roadmap Document" label={t('provenanceLabel')} verified={true} method="PI-planned" timestamp="2024-12-01">
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
          evidence={['PI planning', 'Dependency mapping', 'Capacity planning']}
          limits={['Estimates not commitments', 'External dependencies', 'Resource constraints']}
          next={['Quarterly PI planning', 'Add risk register', 'Publish velocity metrics']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('milestones')}</h2>
        <div className="space-y-4">
          {MOCK_MILESTONES.map(m => (
            <Card key={m.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 rounded bg-forest/10 text-forest font-mono text-sm">{m.quarter}</span>
                    <h3 className="font-medium text-ink">{m.title}</h3>
                    <StatusDot state={m.status === 'completed' ? 'ok' : m.status === 'in-progress' ? 'warn' : 'down'} label={common(m.status)} />
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{m.description}</p>
                  {m.dependencies.length > 0 && (
                    <p className="text-xs text-ink-soft mt-1">{t('dependsOn')}: {m.dependencies.join(', ')}</p>
                  )}
                </div>
                <ProvenanceStamp source="PI Planning" verified={true} method="Agile" timestamp="2024-12-01" label={m.quarter} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}