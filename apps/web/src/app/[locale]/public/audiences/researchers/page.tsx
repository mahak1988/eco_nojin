import { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type RegistryModel = { slug: string; domain: string; fidelity: string; reference: string };

type ModelsIndex = { count: number; models: RegistryModel[] };

type CitationItem = { slug: string; reference: string; doi: string | null };

type CitationIndex = { count: number; items: CitationItem[] };

const TITLES: Record<string, string> = { fa: 'پژوهشگران', en: 'Researchers' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'رجیستری مدل‌ها و مرجع علمی هر مدل',
  en: 'The model registry and the scientific reference behind each model',
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
      url: `${BASE_URL}/${locale}/public/audiences/researchers`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/audiences/researchers`,
      languages: {
        fa: `${BASE_URL}/fa/public/audiences/researchers`,
        en: `${BASE_URL}/en/public/audiences/researchers`,
      },
    },
  };
}

export default async function ResearchersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const models = await apiGet<ModelsIndex>('/api/v1/models');
  const modelsState = toDataState(
    '/api/v1/models',
    models,
    models.ok ? models.data.models.length : 0,
  );
  const citations = await apiGet<CitationIndex>('/api/v1/science/citations/index');
  const citationsState = toDataState(
    '/api/v1/science/citations/index',
    citations,
    citations.ok ? citations.data.items.length : 0,
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={'/api/v1/models'}
          label={title}
          verified={models.ok}
          method={'/api/v1/models'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/models'}</h2>
        <DataStateCard state={modelsState} />
        {modelsState.kind === 'ready' && models.ok ? (
          <>
            <div className="num mb-4 text-3xl font-semibold text-ink">{models.data.count}</div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {models.data.models.map((model) => (
                <Card key={model.slug} density="compact">
                  <h3 className="font-mono text-sm font-medium text-ink">{model.slug}</h3>
                  <p className="mt-1 text-xs text-ink-soft">
                    {model.domain} · {model.fidelity}
                  </p>
                  <div className="mt-2">
                    <ProvenanceStamp
                      source={'/api/v1/models'}
                      verified
                      method={model.slug}
                      label={model.reference}
                    />
                  </div>
                </Card>
              ))}
            </div>
          </>
        ) : null}
        <SourceFooter state={modelsState} />
      </section>

      <section className="mx-auto max-w-5xl px-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/science/citations/index'}</h2>
        <DataStateCard state={citationsState} />
        {citationsState.kind === 'ready' && citations.ok ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {citations.data.items.map((item) => (
              <Card key={item.slug} density="compact">
                <h3 className="font-mono text-sm font-medium text-ink">{item.slug}</h3>
                <p className="mt-1 text-sm text-ink-soft">{item.reference}</p>
                <div className="mt-2">
                  <ProvenanceStamp
                    source={'/api/v1/science/citations/index'}
                    verified={Boolean(item.doi)}
                    method={item.slug}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={citationsState} />
      </section>
    </main>
  );
}
