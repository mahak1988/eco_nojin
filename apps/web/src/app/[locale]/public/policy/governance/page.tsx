import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface GovernanceBody {
  id: string;
  name: string;
  role: string;
  composition: string;
  authority: string;
  meets: string;
  source: string;
}

const MOCK_BODIES: GovernanceBody[] = [
  { id: 'g1', name: 'Eco Nojin Foundation Board', role: 'Strategic oversight & fiduciary duty', composition: '7 members (3 independent, 2 community, 2 technical)', authority: 'Approve budget, strategy, key appointments', meets: 'Quarterly', source: 'Foundation Charter' },
  { id: 'g2', name: 'Technical Steering Committee', role: 'Architecture & standards governance', composition: '9 members (lead engineers, domain experts)', authority: 'Approve ADRs, API contracts, release criteria', meets: 'Bi-weekly', source: 'TSC Charter' },
  { id: 'g3', name: 'Ethics & Compliance Board', role: 'AI ethics, data governance, regulatory compliance', composition: '5 members (legal, ethics, community, technical)', authority: 'Review high-risk features, approve data policies', meets: 'Monthly', source: 'Ethics Charter' },
  { id: 'g4', name: 'Community Council', role: 'User representation & feedback loop', composition: '15 delegates (regional, linguistic, sectoral)', authority: 'Advisory on roadmap, UX, localization', meets: 'Monthly', source: 'Community Charter' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'سازماندهی حکمرانی', en: 'Governance Structure' };
  const descriptions: Record<string, string> = { fa: 'سازماندهی و بدنه‌های تصمیم‌گیری پلتفرم', en: 'Platform governance bodies and decision structures' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/governance`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/governance`, languages: { fa: `${BASE_URL}/fa/public/policy/governance`, en: `${BASE_URL}/en/public/policy/governance` } },
  };
}

export default async function GovernancePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.governance');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Governance Registry" label={t('provenanceLabel')} verified={true} method="Charter-defined" timestamp="2024-12-01">
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
          evidence={['Charter-defined mandates', 'Transparent meeting minutes', 'Conflict-of-interest policies']}
          limits={['Regional legal variations', 'Enforcement mechanisms evolving', 'Community council scaling']}
          next={['Publish meeting transcripts', 'Add decision registry', 'Automate COI declarations']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('bodiesCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_BODIES.map(body => (
            <Card key={body.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{body.name}</h3>
                  <p className="text-sm text-ink-soft mt-1">{body.role}</p>
                  <p className="text-xs text-ink-soft">Composition: {body.composition}</p>
                  <p className="text-xs text-ink-soft">Meets: {body.meets}</p>
                </div>
                <ProvenanceStamp source={body.source} verified={true} label={body.authority} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}