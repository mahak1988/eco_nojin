import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface DisputeFeature {
  id: string;
  name: string;
  description: string;
  status: 'live' | 'beta' | 'planned';
  apiEndpoint: string;
  source: string;
}

const MOCK_FEATURES: DisputeFeature[] = [
  { id: 'df1', name: 'Case Filing', description: 'Structured evidence submission', status: 'live', apiEndpoint: 'POST /api/disputes', source: 'dispute_resolution service' },
  { id: 'df2', name: 'Evidence Review', description: 'Multi-party document review', status: 'live', apiEndpoint: 'GET /api/disputes/:id/evidence', source: 'dispute_resolution service' },
  { id: 'df3', name: 'Arbitration Panel', description: '3-5 arbitrator selection', status: 'live', apiEndpoint: 'POST /api/disputes/:id/panel', source: 'arbitration service' },
  { id: 'df4', name: 'Verdict & Enforcement', description: 'Binding decision with escrow release', status: 'beta', apiEndpoint: 'POST /api/disputes/:id/verdict', source: 'arbitration service' },
  { id: 'df5', name: 'Appeals Process', description: 'Escalation to bazaar/platform', status: 'planned', apiEndpoint: 'POST /api/disputes/:id/appeal', source: 'governance service' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'نمایشگاه حل اختلاف', en: 'Dispute Resolution Demo' };
  const descriptions: Record<string, string> = { fa: 'فرآیند داوری و حل منازعات', en: 'Arbitration and dispute resolution workflow' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/dispute-resolution`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/dispute-resolution`, languages: { fa: `${BASE_URL}/fa/public/components/dispute-resolution`, en: `${BASE_URL}/en/public/components/dispute-resolution` } },
  };
}

export default async function DisputeResolutionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.disputeResolution');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Dispute Registry" label={t('provenanceLabel')} verified={true} method="Case-logged" timestamp="2024-12-10">
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
          evidence={['Evidence-based workflow', 'Multi-arbitrator panel', 'Escrow-linked enforcement']}
          limits={['Appeals not live', 'Cross-border enforcement WIP', 'Legal aid integration missing']}
          next={['Enable appeals', 'Add legal aid directory', 'Automate enforcement']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('features')}</h2>
        <div className="grid gap-4">
          {MOCK_FEATURES.map(f => (
            <Card key={f.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{f.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {f.status === 'live' ? 'bg-forest/10 text-forest' :
                       f.status === 'beta' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {f.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{f.description}</p>
                  <p className="text-xs text-ink-soft font-mono">{f.apiEndpoint}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={f.status === 'live' ? 'ok' : f.status === 'beta' ? 'warn' : 'down'} label={common(f.status)} />
                  <ProvenanceStamp source={f.source} verified={true} method="OpenAPI" label={f.status} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}