import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ResearchBreadcrumb } from '@/components/research/ResearchBreadcrumb';
import {
  ContractList,
  RecordList,
  type ResearchFact,
  type ResearchRecord,
  SummaryList,
  UnavailableNotice,
} from '@/components/research/ResearchParts';
import {
  ResearchWorkspaceShell,
  type WorkspaceTabItem,
} from '@/components/research/ResearchWorkspaceShell';
import {
  isExperimentCapabilityWired,
  isResearchExperimentId,
  RESEARCH_CITATIONS_ENDPOINT,
  RESEARCH_DATASETS_ENDPOINT,
  RESEARCH_DOI_ENDPOINT,
  RESEARCH_ROUTE_ID,
  RESEARCH_ROUTE_PATTERN,
  RESEARCH_WORKSPACE_PANELS,
  researchCapability,
  resolvePanelState,
} from '@/components/research/registry';
import { StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';
import {
  BACK_LABEL_KEY,
  CONTRACT_DETAIL_LABEL_KEY,
  CONTRACT_LABEL_KEY,
  ENDPOINT_LABEL_KEY,
  isCapabilityWired,
  RESEARCH_WORKSPACE_ROUTE,
  RESULT_LABEL_KEY,
  SERVICE_LABEL_KEY,
  SOURCE_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_DETAIL_KEY,
  UNAVAILABLE_LABEL_KEY,
  UNAVAILABLE_TITLE_KEY,
} from '@/lib/domains/registry';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://app.eco-nojin.org';

// Experiment identity, datasets and citations are re-resolved on every request.
export const dynamic = 'force-dynamic';

const SECTIONS_HEADING_ID = 'research-workspace-sections';

type DatasetCatalog = {
  count: number;
  live: number;
  datasets: {
    id: string;
    name: string;
    domain: string;
    source: string;
    status: string;
    requires: string;
    license: string;
  }[];
};

type CitationIndex = {
  count: number;
  items: {
    slug: string;
    name_fa: string;
    name_en: string;
    reference: string | null;
    doi: string | null;
  }[];
};

type ZenodoStatus = { configured: boolean; status: string };

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; experimentId: string }>;
}): Promise<Metadata> {
  const { locale, experimentId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: `${experimentId} · ${t(RESEARCH_WORKSPACE_ROUTE.headingKey)}`,
    description: t('evidence.lead'),
    // Experiment records are not published; the workspace stays out of the index.
    robots: { index: false, follow: false },
    alternates: {
      canonical: `${BASE_URL}/${locale}/research/workspace/${encodeURIComponent(experimentId)}`,
    },
  };
}

export default async function ResearchWorkspacePage({
  params,
}: {
  params: Promise<{ locale: string; experimentId: string }>;
}) {
  const { locale, experimentId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  if (!isResearchExperimentId(experimentId)) notFound();

  const [datasets, citations, doi] = await Promise.all([
    apiGet<DatasetCatalog>(RESEARCH_DATASETS_ENDPOINT),
    apiGet<CitationIndex>(RESEARCH_CITATIONS_ENDPOINT),
    apiGet<ZenodoStatus>(RESEARCH_DOI_ENDPOINT),
  ]);

  const unavailable = t(UNAVAILABLE_LABEL_KEY);
  const usePersianName = locale === 'fa';
  const modelName = (item: CitationIndex['items'][number]) =>
    usePersianName ? item.name_fa : item.name_en;

  // No experiment contract is registered, so the identity never reports a run.
  const experimentCapabilityWired = isExperimentCapabilityWired('research-experiments');

  const workspaceContracts = RESEARCH_WORKSPACE_ROUTE.capabilities.map((capability) => ({
    id: capability.id,
    label: t(capability.labelKey),
    endpoint: capability.endpoint,
    state: isCapabilityWired(capability) ? ('warn' as const) : ('down' as const),
    stateLabel: isCapabilityWired(capability) ? t('common.planned') : unavailable,
  }));

  const identity: ResearchFact[] = [
    {
      id: 'experiment',
      label: t(RESEARCH_WORKSPACE_ROUTE.headingKey),
      value: experimentId,
    },
    { id: 'route', label: t(SERVICE_LABEL_KEY), value: RESEARCH_ROUTE_ID },
    { id: 'pattern', label: t('market.template.method'), value: RESEARCH_ROUTE_PATTERN },
    { id: 'access', label: t(STATE_LABEL_KEY), value: RESEARCH_WORKSPACE_ROUTE.access },
    { id: 'owner', label: t('common.audienceLabel'), value: RESEARCH_WORKSPACE_ROUTE.owner },
    { id: 'origin', label: t(SOURCE_LABEL_KEY), value: RESEARCH_WORKSPACE_ROUTE.sourceOfTruth },
  ];

  const datasetRecords: ResearchRecord[] = datasets.ok
    ? datasets.data.datasets.map((dataset) => ({
        id: dataset.id,
        title: dataset.name,
        technical: dataset.id,
        state: dataset.status === 'live' ? ('ok' as const) : ('down' as const),
        stateLabel: dataset.status,
        facts: [
          { id: 'domain', label: t('market.bazaar.type'), value: dataset.domain },
          { id: 'source', label: t('auth.common.provenance.source'), value: dataset.source },
          { id: 'requires', label: t('auth.common.provenance.method'), value: dataset.requires },
          { id: 'license', label: t('legal.title'), value: dataset.license },
        ],
      }))
    : [];

  const citationRecords: ResearchRecord[] = citations.ok
    ? citations.data.items.map((item) => ({
        id: item.slug,
        title: modelName(item),
        technical: item.slug,
        facts: [
          { id: 'reference', label: t('auth.common.provenance.source'), value: item.reference },
          // The gateway answers `doi: null` until a DOI is actually issued.
          { id: 'doi', label: t('common.evidence'), value: item.doi },
        ],
      }))
    : [];

  const tabs: WorkspaceTabItem[] = RESEARCH_WORKSPACE_PANELS.map((panel) => {
    const detail = t(panel.detailKey);
    const endpoint = panel.sourceEndpoint ?? unavailable;
    const notice = () => (
      <UnavailableNotice title={t(UNAVAILABLE_TITLE_KEY)} detail={t(UNAVAILABLE_DETAIL_KEY)} />
    );

    if (panel.id === 'datasets') {
      return {
        id: panel.id,
        label: t(panel.headingKey),
        content: (
          <>
            <p className="text-sm text-ink-soft">{detail}</p>
            <p className="num text-xs text-ink-faint">
              {t(ENDPOINT_LABEL_KEY)}: {endpoint}
            </p>
            <RecordList
              label={t('auth.common.provenance.source')}
              items={datasetRecords}
              unavailableLabel={unavailable}
              emptyLabel={datasets.ok ? t('learn.emptyDesc') : unavailable}
            />
            {notice()}
          </>
        ),
      };
    }

    if (panel.id === 'runs') {
      const capability = researchCapability(panel.capabilityId);
      return {
        id: panel.id,
        label: t(panel.headingKey),
        content: (
          <>
            <p className="text-sm text-ink-soft">{detail}</p>
            <SummaryList
              items={[
                { id: 'capability', label: t(SERVICE_LABEL_KEY), value: capability?.id ?? null },
                {
                  id: 'endpoint',
                  label: t(ENDPOINT_LABEL_KEY),
                  value: capability?.endpoint ?? null,
                },
                { id: 'result', label: t(RESULT_LABEL_KEY), value: null },
              ]}
              unavailableLabel={unavailable}
            />
            {notice()}
          </>
        ),
      };
    }

    if (panel.id === 'validation') {
      return {
        id: panel.id,
        label: t(panel.headingKey),
        content: (
          <>
            <p className="text-sm text-ink-soft">{detail}</p>
            <p className="field-label">{t('common.evidenceLabel')}</p>
            <ul className="mt-2 list-inside list-disc space-y-2 text-sm text-ink">
              {(t.raw('evidence.evidence') as string[]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            {notice()}
          </>
        ),
      };
    }

    const state = resolvePanelState(panel, citations.ok);
    return {
      id: panel.id,
      label: t(panel.headingKey),
      content: (
        <>
          <p className="text-sm text-ink-soft">{detail}</p>
          <p className="num text-xs text-ink-faint">
            {t(ENDPOINT_LABEL_KEY)}: {endpoint}
          </p>
          <SummaryList
            items={[
              { id: 'doi-endpoint', label: t(SOURCE_LABEL_KEY), value: RESEARCH_DOI_ENDPOINT },
              {
                id: 'doi-state',
                label: t(STATE_LABEL_KEY),
                value: doi.ok && doi.data.configured ? doi.data.status : null,
              },
            ]}
            unavailableLabel={unavailable}
          />
          <RecordList
            label={t('science.modelsTitle')}
            items={citationRecords}
            unavailableLabel={unavailable}
            emptyLabel={citations.ok ? t('learn.emptyDesc') : unavailable}
          />
          <p className="text-xs text-ink-soft">
            {state === 'available' ? t('statusLine.realData') : t(UNAVAILABLE_DETAIL_KEY)}
          </p>
        </>
      ),
    };
  });

  return (
    <div>
      <ResearchBreadcrumb
        label={t('nav.science')}
        items={[
          { id: 'research', href: `/${locale}/research`, label: t('evidence.title') },
          { id: 'experiment', label: experimentId, current: true },
        ]}
      />

      <header className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="num text-xs text-ink-faint">
            /{locale}/research/workspace/{experimentId}
          </p>
          <h1 className="display text-3xl font-bold break-all text-ink sm:text-4xl">
            {experimentId}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('evidence.lead')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusDot
            state={experimentCapabilityWired ? 'warn' : 'down'}
            label={experimentCapabilityWired ? t('common.planned') : unavailable}
          />
          <Link href={`/${locale}/research`} className="btn btn-ghost">
            {t(BACK_LABEL_KEY)}
          </Link>
        </div>
      </header>

      <div className="mt-4">
        <UnavailableNotice title={t(UNAVAILABLE_TITLE_KEY)} detail={t(UNAVAILABLE_DETAIL_KEY)} />
      </div>

      <ResearchWorkspaceShell
        labelledBy={SECTIONS_HEADING_ID}
        sectionsLabel={t('evidence.title')}
        contextLabel={t(CONTRACT_LABEL_KEY)}
        context={
          <>
            <SummaryList items={identity} unavailableLabel={unavailable} columns={3} />
            <p className="field-label">{t(SERVICE_LABEL_KEY)}</p>
            <ContractList
              items={workspaceContracts}
              endpointLabel={t(ENDPOINT_LABEL_KEY)}
              unavailableLabel={unavailable}
            />
            <p className="text-xs text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
          </>
        }
        tabs={tabs}
      />
    </div>
  );
}
