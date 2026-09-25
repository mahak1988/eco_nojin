import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const TOOL_REGISTRY_PATH = '/api/v1/tool-registry';
const PLATFORM_HEALTH_PATH = '/api/v1/platform/health';

type PlatformHealth = {
  status: string;
  service: string;
  cpp_available: boolean;
  db_backend: string;
  db_reachable: boolean;
};

type RegistryTool = {
  tool_id: string;
  domain: string;
  category: string;
  endpoint_path: string;
  is_active: boolean;
};

type ToolRegistry = {
  count: number;
  tools: RegistryTool[];
};

export const dynamic = 'force-dynamic';

export default async function APIAccessPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const developers = await getTranslations('developers');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const [health, registry] = await Promise.all([
    apiGet<PlatformHealth>(PLATFORM_HEALTH_PATH),
    apiGet<ToolRegistry>(TOOL_REGISTRY_PATH),
  ]);
  const tools = registry.ok ? registry.data.tools : [];
  const count = registry.ok ? registry.data.count : 0;

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={TOOL_REGISTRY_PATH}
          label={developers('title')}
          verified={registry.ok}
          method={TOOL_REGISTRY_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{developers('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{developers('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{developers('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{developers('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {health.ok ? (
          <Card density="compact">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-sm font-medium text-ink">
                  {health.data.service} · {health.data.db_backend}
                </h2>
                <p className="mt-1 text-xs text-ink-soft">
                  cpp_available: {String(health.data.cpp_available)} · db_reachable:{' '}
                  {String(health.data.db_reachable)}
                </p>
              </div>
              <ProvenanceStamp
                source={PLATFORM_HEALTH_PATH}
                verified={health.ok}
                method={PLATFORM_HEALTH_PATH}
              />
            </div>
          </Card>
        ) : (
          <Card density="compact">
            <h2 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {health.error}
            </p>
          </Card>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{TOOL_REGISTRY_PATH}</h2>
        {tools.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {registry.ok ? '' : ` · ${registry.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className="px-3 py-2 text-start font-medium text-ink-soft">tool_id</th>
                    <th className="px-3 py-2 text-start font-medium text-ink-soft">endpoint</th>
                    <th className="px-3 py-2 text-start font-medium text-ink-soft">domain</th>
                    <th className="px-3 py-2 text-start font-medium text-ink-soft">category</th>
                  </tr>
                </thead>
                <tbody>
                  {tools.map((tool) => (
                    <tr key={tool.tool_id} className="border-b border-line/50">
                      <td className="px-3 py-2 font-mono text-ink">{tool.tool_id}</td>
                      <td className="px-3 py-2 font-mono text-ink-soft">
                        {tool.endpoint_path ?? t('unavailable')}
                      </td>
                      <td className="px-3 py-2 text-ink-soft">{tool.domain}</td>
                      <td className="px-3 py-2 text-ink-soft">{tool.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {TOOL_REGISTRY_PATH} · {t('realData')} · {count}
            </p>
          </>
        )}
      </section>

      <OwnerFooter />
    </main>
  );
}
