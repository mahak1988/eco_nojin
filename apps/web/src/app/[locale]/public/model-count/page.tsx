import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const MODELS_PATH = '/api/v1/models';
const CPP_PATH = '/api/v1/models/cpp-status';
const PINN_PATH = '/api/v1/models/pinn-status';
const REGISTRY_PATH = '/api/v1/tool-registry';

type RegistryModel = {
  slug: string;
  domain: string;
  fidelity: string;
  reference: string;
  validation_status: string | null;
};

type ModelsIndex = {
  count: number;
  fidelity_counts: Record<string, number>;
  models: RegistryModel[];
};

type CppStatus = { available: boolean; dll: string | null; kernels: string[]; note?: string };

type PinnStatus = { available: boolean; note?: string };

type ToolRegistry = { count: number };

const TITLES: Record<string, string> = { fa: 'شمارش مدل‌ها', en: 'Model Count' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تعداد و وضعیت مدل‌های علمی ثبت‌شده',
  en: 'Registered scientific models count and status',
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
      url: `${BASE_URL}/${locale}/public/model-count`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/model-count`,
      languages: {
        fa: `${BASE_URL}/fa/public/model-count`,
        en: `${BASE_URL}/en/public/model-count`,
      },
    },
  };
}

export default async function ModelCountPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const common = await getTranslations('common');
  const science = await getTranslations('science');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [registry, cpp, pinn, tools] = await Promise.all([
    apiGet<ModelsIndex>(MODELS_PATH),
    apiGet<CppStatus>(CPP_PATH),
    apiGet<PinnStatus>(PINN_PATH),
    apiGet<ToolRegistry>(REGISTRY_PATH),
  ]);
  const models = registry.ok ? registry.data.models : [];
  const state = toDataState(MODELS_PATH, registry, models.length);

  const byDomain = new Map<string, number>();
  for (const model of models) {
    byDomain.set(model.domain, (byDomain.get(model.domain) ?? 0) + 1);
  }
  const domains = Array.from(byDomain.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  const fidelityCounts = registry.ok ? Object.entries(registry.data.fidelity_counts) : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={MODELS_PATH}
          label={title}
          verified={registry.ok}
          method={MODELS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{science('modelsTitle')}</h2>
        <DataStateCard
          state={state}
          emptyTitle={science('modelsEmpty')}
          emptyDescription={science('modelsPublicNote')}
        />
        {state.kind === 'ready' && registry.ok ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">{registry.data.count}</div>
                <p className="mt-1 text-sm text-ink-soft">{MODELS_PATH}</p>
                <ProvenanceStamp source={MODELS_PATH} verified method={MODELS_PATH} />
              </Card>
              {fidelityCounts.map(([fidelity, count]) => (
                <Card key={fidelity} density="compact">
                  <div className="num text-3xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">{fidelity}</p>
                  <ProvenanceStamp
                    source={MODELS_PATH}
                    verified={false}
                    method={MODELS_PATH}
                    label={fidelity}
                  />
                </Card>
              ))}
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {domains.map(([domain, count]) => (
                <Card key={domain} density="compact">
                  <div className="num text-2xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">{domain}</p>
                </Card>
              ))}
            </div>
          </>
        ) : null}
        <SourceFooter state={state} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{REGISTRY_PATH}</h2>
        {tools.ok ? (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="num text-3xl font-semibold text-ink">{tools.data.count}</p>
              <ProvenanceStamp source={REGISTRY_PATH} verified method={REGISTRY_PATH} />
            </div>
          </Card>
        ) : (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-medium text-ink">{status('unavailable')}</h3>
              <StatusDot state="down" label={status('unavailable')} />
            </div>
            <p className="mt-1 text-sm text-ink-soft">
              {REGISTRY_PATH} · {tools.error}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={REGISTRY_PATH} verified={false} method={REGISTRY_PATH} />
            </div>
          </Card>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">{CPP_PATH}</p>
              <StatusDot
                state={cpp.ok && cpp.data.available ? 'ok' : 'warn'}
                label={cpp.ok && cpp.data.available ? common('live') : status('unavailable')}
              />
            </div>
            <p className="mt-1 text-xs text-ink-soft">
              {cpp.ok
                ? (cpp.data.note ?? cpp.data.kernels.join(', '))
                : `${CPP_PATH} · ${cpp.error}`}
            </p>
            <ProvenanceStamp source={CPP_PATH} verified={cpp.ok} method={CPP_PATH} />
          </Card>
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">{PINN_PATH}</p>
              <StatusDot
                state={pinn.ok && pinn.data.available ? 'ok' : 'warn'}
                label={pinn.ok && pinn.data.available ? common('live') : status('unavailable')}
              />
            </div>
            <p className="mt-1 text-xs text-ink-soft">
              {pinn.ok ? pinn.data.note : `${PINN_PATH} · ${pinn.error}`}
            </p>
            <ProvenanceStamp source={PINN_PATH} verified={pinn.ok} method={PINN_PATH} />
          </Card>
        </div>
      </section>
    </main>
  );
}
