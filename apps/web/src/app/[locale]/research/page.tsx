import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import {
  ContractList,
  RecordList,
  type ResearchRecord,
  SummaryList,
  UnavailableNotice,
} from '@/components/research/ResearchParts';
import {
  RESEARCH_CITATIONS_ENDPOINT,
  RESEARCH_DATASETS_ENDPOINT,
  RESEARCH_DOI_ENDPOINT,
  RESEARCH_ROUTE_ID,
  RESEARCH_ROUTE_PATTERN,
  researchCapability,
  resolveSourceState,
} from '@/components/research/registry';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import {
  CONTRACT_DETAIL_LABEL_KEY,
  CONTRACT_LABEL_KEY,
  ENDPOINT_LABEL_KEY,
  isCapabilityWired,
  NEXT_DETAIL_KEY,
  NEXT_LABEL_KEY,
  RESEARCH_WORKSPACE_ROUTE,
  SERVICE_LABEL_KEY,
  SOURCE_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_DETAIL_KEY,
  UNAVAILABLE_LABEL_KEY,
  UNAVAILABLE_TITLE_KEY,
} from '@/lib/domains/registry';

// Datasets, citations and the workspace contract are re-resolved per request.
export const dynamic = 'force-dynamic';

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

/** Every path below is registered in the API gateway; nothing is invented here. */
const RESEARCH_SOURCES = [
  RESEARCH_DATASETS_ENDPOINT,
  RESEARCH_CITATIONS_ENDPOINT,
  RESEARCH_DOI_ENDPOINT,
] as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(RESEARCH_WORKSPACE_ROUTE.headingKey),
    description: t('evidence.lead'),
    // Research records are not published; the index stays out of the index.
    robots: { index: false, follow: false },
    alternates: { canonical: `${BASE_URL}/${locale}/research` },
  };
}

export default async function ResearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [datasets, citations, doi] = await Promise.all([
    apiGet<DatasetCatalog>(RESEARCH_DATASETS_ENDPOINT),
    apiGet<CitationIndex>(RESEARCH_CITATIONS_ENDPOINT),
    apiGet<ZenodoStatus>(RESEARCH_DOI_ENDPOINT),
  ]);

  const unavailable = t(UNAVAILABLE_LABEL_KEY);
  const usePersianName = locale === 'fa';
  const modelName = (item: CitationIndex['items'][number]) =>
    usePersianName ? item.name_fa : item.name_en;

  const datasetState = resolveSourceState(RESEARCH_DATASETS_ENDPOINT, datasets.ok);
  const citationState = resolveSourceState(RESEARCH_CITATIONS_ENDPOINT, citations.ok);
  const doiState = resolveSourceState(RESEARCH_DOI_ENDPOINT, doi.ok);
  const liveSources = [datasets, citations, doi].filter((result) => result.ok).length;

  const workspaceContracts = RESEARCH_WORKSPACE_ROUTE.capabilities.map((capability) => ({
    id: capability.id,
    label: t(capability.labelKey),
    endpoint: capability.endpoint,
    state: isCapabilityWired(capability) ? ('warn' as const) : ('down' as const),
    stateLabel: isCapabilityWired(capability) ? t('common.planned') : unavailable,
  }));

  const sourceRows = [
    { id: RESEARCH_DATASETS_ENDPOINT, state: datasetState },
    { id: RESEARCH_CITATIONS_ENDPOINT, state: citationState },
    { id: RESEARCH_DOI_ENDPOINT, state: doiState },
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
    ? citations.data.items.slice(0, 8).map((item) => ({
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

  return (
    <div>
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(RESEARCH_WORKSPACE_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('evidence.lead')}</p>
      </header>

      <div className="mt-6 grid min-w-0 gap-4 lg:grid-cols-2 lg:items-start">
        <section className="card min-w-0 p-5" aria-labelledby="research-workspace-contract">
          <h2 id="research-workspace-contract" className="field-label">
            {t(CONTRACT_LABEL_KEY)}
          </h2>
          <div className="mt-3 space-y-4">
            <SummaryList
              items={[
                { id: 'route', label: t(SERVICE_LABEL_KEY), value: RESEARCH_ROUTE_ID },
                { id: 'access', label: t(STATE_LABEL_KEY), value: RESEARCH_WORKSPACE_ROUTE.access },
                {
                  id: 'owner',
                  label: t('common.audienceLabel'),
                  value: RESEARCH_WORKSPACE_ROUTE.owner,
                },
                {
                  id: 'origin',
                  label: t(SOURCE_LABEL_KEY),
                  value: RESEARCH_WORKSPACE_ROUTE.sourceOfTruth,
                },
              ]}
              unavailableLabel={unavailable}
              columns={4}
            />
            <p className="text-xs text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
            <ContractList
              items={workspaceContracts}
              endpointLabel={t(ENDPOINT_LABEL_KEY)}
              unavailableLabel={unavailable}
            />
          </div>
        </section>

        <section className="card min-w-0 p-5" aria-labelledby="research-sources">
          <h2 id="research-sources" className="field-label">
            {t(ENDPOINT_LABEL_KEY)}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
          <ul className="mt-3 space-y-2">
            {sourceRows.map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-m)] border border-[var(--line)] px-4 py-3"
              >
                <span className="num min-w-0 truncate text-xs text-ink">{row.id}</span>
                <span
                  className={
                    row.state === 'available' ? 'text-xs text-moss' : 'text-xs text-copper'
                  }
                >
                  {row.state === 'available' ? t('statusLine.realData') : unavailable}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-ink-soft">
            {liveSources === RESEARCH_SOURCES.length
              ? t('statusLine.realData')
              : t(UNAVAILABLE_DETAIL_KEY)}
          </p>
        </section>
      </div>

      <div className="mt-4">
        <UnavailableNotice title={t(UNAVAILABLE_TITLE_KEY)} detail={t(UNAVAILABLE_DETAIL_KEY)} />
      </div>

      <section className="card mt-4 p-5" aria-labelledby="research-workspace-route">
        <h2 id="research-workspace-route" className="field-label">
          {t('common.audienceLabel')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('evidence.audience')}</p>
        <p className="num mt-3 text-xs text-ink-faint">
          {t('market.template.method')}: {RESEARCH_ROUTE_PATTERN}/workspace/[experimentId]
        </p>
        <p className="mt-2 text-sm text-ink-soft">{t(UNAVAILABLE_DETAIL_KEY)}</p>
        <p className="num mt-2 text-xs text-ink-faint">
          {t(ENDPOINT_LABEL_KEY)}:{' '}
          {researchCapability('research-experiments')?.endpoint ?? unavailable}
        </p>
      </section>

      <section className="mt-4" aria-labelledby="research-datasets">
        <h2 id="research-datasets" className="field-label">
          {t('public.science.evidenceBase.evidenceCatalog')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
        <RecordList
          label={t('auth.common.provenance.source')}
          items={datasetRecords}
          unavailableLabel={unavailable}
          emptyLabel={datasets.ok ? t('learn.emptyDesc') : unavailable}
        />
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <RecordList
          label={t('science.modelsTitle')}
          items={citationRecords}
          unavailableLabel={unavailable}
          emptyLabel={citations.ok ? t('learn.emptyDesc') : unavailable}
        />
        <div className="card p-5">
          <p className="field-label">{t('trust.title')}</p>
          <p className="mt-2 text-sm text-ink-soft">{t('trust.lead')}</p>
          <p className="num mt-3 text-xs text-ink-faint">
            {t(ENDPOINT_LABEL_KEY)}: {RESEARCH_DOI_ENDPOINT}
          </p>
          <p className="mt-2 text-xs text-ink-soft">
            {doiState === 'available' && doi.ok && doi.data.configured
              ? doi.data.status
              : unavailable}
          </p>
        </div>
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="card p-5">
          <h2 className="field-label">{t(SERVICE_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
          <p className="num mt-3 text-xs text-ink-faint">
            {t(ENDPOINT_LABEL_KEY)}:{' '}
            {researchCapability('research-datasets')?.endpoint ?? unavailable}
          </p>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t(NEXT_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(NEXT_DETAIL_KEY)}</p>
        </div>
      </section>

      <footer className="mt-6 flex flex-wrap items-center gap-3">
        <Link href={`/${locale}/evidence`} className="btn btn-ghost">
          {t('common.evidence')}
        </Link>
        <Link href={`/${locale}/hydroma`} className="btn btn-ghost">
          {t('platformOverview.itemScience')}
        </Link>
        <span className="text-xs text-ink-soft">{t('statusLine.realData')}</span>
      </footer>
    </div>
  );
}
