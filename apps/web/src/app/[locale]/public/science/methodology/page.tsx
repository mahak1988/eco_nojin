import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const MODELS_PATH = '/api/v1/models';

type RegistryModel = {
  slug: string;
  name_fa: string;
  name_en: string;
  domain: string;
  fidelity: string;
  reference: string;
  description: string;
};

type ModelsIndex = {
  count: number;
  fidelity_counts: Record<string, number>;
  models: RegistryModel[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-science-methodology');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/methodology`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/science/methodology'),
      languages: languageAlternates('/public/science/methodology'),
    },
  };
}

export default async function MethodologyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-science-methodology');
  const title = meta('title');
  const description = meta('description');

  const registry = await apiGet<ModelsIndex>(MODELS_PATH);
  const models = registry.ok ? registry.data.models : [];
  const state = toDataState(MODELS_PATH, registry, models.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={MODELS_PATH}
            label={title}
            verified={registry.ok}
            method={MODELS_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{MODELS_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
          <div className="grid gap-4">
            {models.map((model) => (
              <Card key={model.slug} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">
                      {locale === 'fa' ? model.name_fa : model.name_en}
                    </h3>
                    <p className="text-sm text-ink-soft mt-1">{model.reference}</p>
                    <p className="text-xs text-ink-soft mt-1">{model.description}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusDot
                      state={model.fidelity === 'official' ? 'ok' : 'warn'}
                      label={model.fidelity}
                    />
                    <ProvenanceStamp
                      source={model.reference}
                      method={model.domain}
                      label={model.slug}
                    />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
