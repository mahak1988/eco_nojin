import { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const TOOL_REGISTRY_PATH = '/api/v1/tool-registry';

type RegistryTool = {
  tool_id: string;
  name_fa: string;
  name_en: string;
  domain: string;
  category: string;
  fidelity: string;
  reference: string;
  endpoint_path: string;
  phase: number | null;
  is_active: boolean;
};

type ToolRegistry = {
  count: number;
  tools: RegistryTool[];
};

const TITLES: Record<string, string> = { fa: 'زمین بازی API', en: 'API Playground' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'کنسول تعاملی برای تست اندپوینت‌ها',
  en: 'Interactive console for testing endpoints',
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
      url: `${BASE_URL}/${locale}/public/components/api-playground`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/api-playground`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/api-playground`,
        en: `${BASE_URL}/en/public/components/api-playground`,
      },
    },
  };
}

export default async function APIPlaygroundPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // The registered tool manifest is the only endpoint inventory the gateway
  // publishes; undocumented paths are never listed here.
  const registry = await apiGet<ToolRegistry>(TOOL_REGISTRY_PATH);
  const tools = registry.ok ? registry.data.tools : [];
  const state = toDataState(TOOL_REGISTRY_PATH, registry, tools.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={TOOL_REGISTRY_PATH}
          label={title}
          verified={registry.ok}
          method={TOOL_REGISTRY_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{TOOL_REGISTRY_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  <th className="px-3 py-2 text-start font-medium text-ink-soft">tool_id</th>
                  <th className="px-3 py-2 text-start font-medium text-ink-soft">endpoint</th>
                  <th className="px-3 py-2 text-start font-medium text-ink-soft">domain</th>
                  <th className="px-3 py-2 text-start font-medium text-ink-soft">fidelity</th>
                </tr>
              </thead>
              <tbody>
                {tools.map((tool) => (
                  <tr key={tool.tool_id} className="border-b border-line/50">
                    <td className="px-3 py-2 font-mono text-ink">{tool.tool_id}</td>
                    <td className="px-3 py-2 font-mono text-ink-soft">
                      {tool.endpoint_path ?? tool.tool_id}
                    </td>
                    <td className="px-3 py-2 text-ink-soft">{tool.domain}</td>
                    <td className="px-3 py-2 text-ink-soft">{tool.fidelity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
