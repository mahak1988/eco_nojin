import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ScientificToolLayout } from '@/components/layout/ScientificToolLayout';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import {
  BACK_LABEL_KEY,
  CONTRACT_DETAIL_LABEL_KEY,
  CONTRACT_LABEL_KEY,
  ENDPOINT_LABEL_KEY,
  findCapability,
  getScientificTool,
  HYDROMA_TOOLS_ROUTE,
  LIVE_LABEL_KEY,
  NEXT_DETAIL_KEY,
  NEXT_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  RESULT_LABEL_KEY,
  resolveCapabilityState,
  resolveExecutionCapability,
  SERVICE_LABEL_KEY,
  SOURCE_LABEL_KEY,
  STATE_LABEL_KEY,
  scientificToolParams,
  UNAVAILABLE_DETAIL_KEY,
  UNAVAILABLE_LABEL_KEY,
  UNAVAILABLE_TITLE_KEY,
} from '@/lib/domains/registry';

type ToolRegistryRecord = {
  tool_id: string;
  name_fa: string | null;
  name_en: string | null;
  domain: string | null;
  category: string | null;
  fidelity: string | null;
  reference: string | null;
  service_slug: string | null;
  endpoint_path: string | null;
  phase: number | null;
  is_active: boolean;
};

const metadataCapability = findCapability(HYDROMA_TOOLS_ROUTE, 'tool-metadata');
const kernelsCapability = findCapability(HYDROMA_TOOLS_ROUTE, 'cpp-kernel-status');

/** Tool ids are known statically; any other id is resolved from the registry. */
export function generateStaticParams() {
  return scientificToolParams();
}

export const dynamicParams = true;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; toolId: string }>;
}): Promise<Metadata> {
  const { locale, toolId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const tool = await apiGet<ToolRegistryRecord>(
    `/api/v1/tool-registry/${encodeURIComponent(toolId)}`,
  );
  const record = tool.ok ? tool.data : null;
  const name = record ? (locale === 'fa' ? record.name_fa : record.name_en) : null;
  const title = name ?? toolId;

  return {
    title: `${title} · ${t(HYDROMA_TOOLS_ROUTE.headingKey)}`,
    description: t(UNAVAILABLE_DETAIL_KEY),
    robots: { index: false, follow: true },
    alternates: {
      canonical: `${BASE_URL}/${locale}/hydroma/tools/${toolId}`,
    },
  };
}

export default async function ScientificToolPage({
  params,
}: {
  params: Promise<{ locale: string; toolId: string }>;
}) {
  const { locale, toolId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const declared = getScientificTool(toolId);
  const [tool, kernels] = await Promise.all([
    apiGet<ToolRegistryRecord>(`/api/v1/tool-registry/${encodeURIComponent(toolId)}`),
    apiGet<{ available: boolean }>('/api/v1/models/cpp-status'),
  ]);

  // Nothing declares this id: it is neither a known tool nor registered.
  if (!declared && !tool.ok) notFound();

  const record = tool.ok ? tool.data : null;
  const metadataState = resolveCapabilityState(metadataCapability, tool.ok);
  const executionEndpoint = record?.endpoint_path ?? declared?.executionEndpoint ?? null;
  const executionState = resolveExecutionCapability(declared, executionEndpoint);
  const kernelsState = resolveCapabilityState(
    kernelsCapability,
    kernels.ok && kernels.data.available,
  );

  const name = record
    ? ((locale === 'fa' ? record.name_fa : record.name_en) ?? record.name_fa ?? record.name_en)
    : null;
  const title = name ?? toolId;

  const facts = [
    {
      id: 'state',
      label: t(STATE_LABEL_KEY),
      value: metadataState === 'available' ? t(LIVE_LABEL_KEY) : null,
    },
    { id: 'endpoint', label: t(ENDPOINT_LABEL_KEY), value: executionEndpoint },
    {
      id: 'source',
      label: t(SOURCE_LABEL_KEY),
      value: metadataState === 'available' ? `/api/v1/tool-registry/${toolId}` : null,
    },
    { id: 'result', label: t(RESULT_LABEL_KEY), value: null },
  ];

  return (
    <ScientificToolLayout
      toolId={toolId}
      title={title}
      lead={t(UNAVAILABLE_DETAIL_KEY)}
      state={executionState}
      stateLabel={executionState === 'available' ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
      unavailableLabel={t(UNAVAILABLE_LABEL_KEY)}
      inputLabel={t(CONTRACT_LABEL_KEY)}
      outputLabel={t(RESULT_LABEL_KEY)}
      metadataLabel={t(SOURCE_LABEL_KEY)}
      replayLabel={t('common.retry')}
      facts={facts}
      inputPanel={
        <div className="space-y-3">
          <p className="text-sm text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
          <dl className="grid gap-2 text-sm">
            {declared ? (
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="text-ink-soft">{t(SERVICE_LABEL_KEY)}</dt>
                <dd className="num text-ink">{declared.sourceOfTruth}</dd>
              </div>
            ) : null}
            {record?.domain ? (
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="text-ink-soft">{t(HYDROMA_TOOLS_ROUTE.headingKey)}</dt>
                <dd className="num text-ink">{record.domain}</dd>
              </div>
            ) : null}
            {record?.fidelity ? (
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="text-ink-soft">{t(CONTRACT_LABEL_KEY)}</dt>
                <dd className="num text-ink">{record.fidelity}</dd>
              </div>
            ) : null}
            {record?.reference ? (
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="text-ink-soft">{t('common.evidence')}</dt>
                <dd className="num text-ink">{record.reference}</dd>
              </div>
            ) : null}
          </dl>
          <p className="text-sm text-ink-soft">{t(UNAVAILABLE_TITLE_KEY)}</p>
          <p className="num text-xs text-ink-faint">{t(UNAVAILABLE_LABEL_KEY)}</p>
        </div>
      }
      outputScene={
        <div className="space-y-3">
          <p className="text-sm text-ink">{t(UNAVAILABLE_TITLE_KEY)}</p>
          <p className="text-sm text-ink-soft">{t(UNAVAILABLE_DETAIL_KEY)}</p>
          <p className="num text-xs text-ink-faint">{t(REAL_DATA_LABEL_KEY)}</p>
        </div>
      }
    >
      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="card p-5">
          <h2 className="field-label">{t(CONTRACT_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t(NEXT_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(NEXT_DETAIL_KEY)}</p>
        </div>
      </section>

      <section className="card mt-4 flex flex-wrap items-center justify-between gap-3 p-5">
        <p className="text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
        <div className="flex flex-wrap items-center gap-3">
          <span className="num text-xs text-ink-faint">
            {kernelsState === 'available' ? t('science.cppOk') : t('science.cppMissing')}
          </span>
          <Link href={`/${locale}/hydroma`} className="btn btn-ghost">
            {t(BACK_LABEL_KEY)}
          </Link>
        </div>
      </section>
    </ScientificToolLayout>
  );
}
