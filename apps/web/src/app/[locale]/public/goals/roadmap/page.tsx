import { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type Gate = {
  name: string;
  requires: string[];
  status: string;
  allowed: boolean;
  reason: string;
};

type PhaseGateStatus = { phase: string; gates: Gate[]; all_passed: boolean };

type ToolRegistryPhase = {
  slug: string;
  title_fa: string;
  title_en: string;
  status: string;
  seq: number;
  description_fa: string;
  description_en: string;
};

type ToolRegistryPhases = { count: number; phases: ToolRegistryPhase[] };

const TITLES: Record<string, string> = { fa: 'نقشه راه', en: 'Roadmap' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'دروازه‌های فاز و فازهای ثبت‌شده در رجیستری ابزار',
  en: 'The registered phase gates and phases in the tool registry',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/goals/roadmap`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/goals/roadmap`,
      languages: {
        fa: `${BASE_URL}/fa/public/goals/roadmap`,
        en: `${BASE_URL}/en/public/goals/roadmap`,
      },
    },
  };
}

export default async function RoadmapPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const gates = await apiGet<PhaseGateStatus>('/api/v1/blockchain/phasegate/status');
  const gatesState = toDataState(
    '/api/v1/blockchain/phasegate/status',
    gates,
    gates.ok ? gates.data.gates.length : 0,
  );
  const phases = await apiGet<ToolRegistryPhases>('/api/v1/tool-registry/phases');
  const phasesState = toDataState(
    '/api/v1/tool-registry/phases',
    phases,
    phases.ok ? phases.data.phases.length : 0,
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={'/api/v1/blockchain/phasegate/status'}
          label={title}
          verified={gates.ok}
          method={'/api/v1/blockchain/phasegate/status'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">
            {'/api/v1/blockchain/phasegate/status'}
          </h2>
          <DataStateCard state={gatesState} />
          {gatesState.kind === 'ready' && gates.ok ? (
            <div className="grid gap-4">
              {gates.data.gates.map((gate) => (
                <Card key={gate.name} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">{gate.name}</h3>
                      <p className="mt-1 text-sm text-ink-soft">{gate.reason}</p>
                      {gate.requires.length > 0 ? (
                        <p className="num mt-1 font-mono text-xs text-ink-soft">
                          {gate.requires.join(' · ')}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusDot state={gate.allowed ? 'ok' : 'down'} label={gate.status} />
                      <ProvenanceStamp
                        source={'/api/v1/blockchain/phasegate/status'}
                        verified={gate.allowed}
                        method={gate.name}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : null}
          <SourceFooter state={gatesState} />
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/tool-registry/phases'}</h2>
          <DataStateCard state={phasesState} />
          {phasesState.kind === 'ready' && phases.ok ? (
            <div className="grid gap-4">
              {phases.data.phases.map((entry) => (
                <Card key={entry.slug} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">
                        {locale === 'fa' ? entry.title_fa : entry.title_en}
                      </h3>
                      <p className="mt-1 text-sm text-ink-soft">
                        {locale === 'fa' ? entry.description_fa : entry.description_en}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusDot
                        state={entry.status === 'active' ? 'ok' : 'warn'}
                        label={entry.status}
                      />
                      <ProvenanceStamp
                        source={'/api/v1/tool-registry/phases'}
                        verified
                        method={entry.slug}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : null}
          <SourceFooter state={phasesState} />
        </section>
      </div>
    </main>
  );
}
