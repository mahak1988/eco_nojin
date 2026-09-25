import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const MODELS_PATH = '/api/v1/models';

type RegistryModel = {
  slug: string;
  domain: string;
  fidelity: string;
};

type ModelsIndex = {
  count: number;
  fidelity_counts: Record<string, number>;
  models: RegistryModel[];
};

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
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const science = await getTranslations('science');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const registry = await apiGet<ModelsIndex>(MODELS_PATH);
  const data = registry.ok ? registry.data : null;
  const models = data ? data.models : [];

  const byDomain = new Map<string, number>();
  for (const model of models) {
    byDomain.set(model.domain, (byDomain.get(model.domain) ?? 0) + 1);
  }
  const domains = Array.from(byDomain.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  const fidelityCounts = data ? Object.entries(data.fidelity_counts) : [];

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

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{science('modelsTitle')}</h2>
        {models.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">
              {registry.ok ? science('modelsEmpty') : template('unavailableTitle')}
            </h3>
            <p className="mt-1 text-sm text-ink-soft">
              {registry.ok ? science('modelsPublicNote') : template('unavailableDescription')}
            </p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {registry.ok ? '' : ` · ${registry.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">{data?.count ?? 0}</div>
                <p className="mt-1 text-sm text-ink-soft">{MODELS_PATH}</p>
                <ProvenanceStamp source={MODELS_PATH} verified={registry.ok} method={MODELS_PATH} />
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
            <h3 className="mt-8 text-sm font-semibold text-ink-soft">{science('modelsTitle')}</h3>
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {domains.map(([domain, count]) => (
                <Card key={domain} density="compact">
                  <div className="num text-2xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">{domain}</p>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {MODELS_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
