import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const CARBON_PATH = '/api/v1/hydroma/carbon';

type CarbonTool = {
  id: string;
  name_en: string;
  description: string;
  reference: string;
};

type CarbonTools = {
  count: number;
  models: CarbonTool[];
};

export const dynamic = 'force-dynamic';

export default async function CarbonRegistryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');

  const carbon = await apiGet<CarbonTools>(CARBON_PATH);
  const tools = carbon.ok ? carbon.data.models : [];
  const state = toDataState(CARBON_PATH, carbon, tools.length);

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CARBON_PATH}
          label={services('title')}
          verified={carbon.ok}
          method={CARBON_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{CARBON_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
          <div className="grid gap-4">
            {tools.map((tool) => (
              <Card key={tool.id} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">{tool.name_en}</h3>
                    <p className="mt-1 text-sm text-ink-soft">{tool.description}</p>
                    <p className="mt-1 text-xs text-ink-soft">{tool.reference}</p>
                  </div>
                  <ProvenanceStamp
                    source={CARBON_PATH}
                    verified={false}
                    method={tool.id}
                    label={tool.reference}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>

      <OwnerFooter />
    </main>
  );
}
