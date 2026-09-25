import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const MODELS_PATH = '/api/v1/models';
const CPP_PATH = '/api/v1/models/cpp-status';
const PINN_PATH = '/api/v1/models/pinn-status';

type RegistryModel = {
  slug: string;
  name_fa: string;
  name_en: string;
  domain: string;
  fidelity: string;
  reference: string;
};

type ModelsIndex = {
  count: number;
  fidelity_counts: Record<string, number>;
  models: RegistryModel[];
};

type CppStatus = {
  available: boolean;
  dll: string | null;
  kernels: string[];
  note?: string;
};

type PinnStatus = {
  available: boolean;
  note?: string;
};

const TITLES: Record<string, string> = { fa: 'موتور هیدروما', en: 'HydroMa Engine' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'نمایشگر ماژول‌های موتور علمی',
  en: 'Scientific engine module showcase',
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
      url: `${BASE_URL}/${locale}/public/components/hydroma-engine`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/hydroma-engine`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/hydroma-engine`,
        en: `${BASE_URL}/en/public/components/hydroma-engine`,
      },
    },
  };
}

export default async function HydromaEnginePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const science = await getTranslations('science');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [registry, cpp, pinn] = await Promise.all([
    apiGet<ModelsIndex>(MODELS_PATH),
    apiGet<CppStatus>(CPP_PATH),
    apiGet<PinnStatus>(PINN_PATH),
  ]);
  const models = registry.ok ? registry.data.models : [];

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
        <div className="grid gap-4 sm:grid-cols-2">
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">{science('cppOk')}</p>
              <StatusDot
                state={cpp.ok && cpp.data.available ? 'ok' : 'warn'}
                label={cpp.ok && cpp.data.available ? 'live' : 'unavailable'}
              />
            </div>
            <p className="mt-1 text-xs text-ink-soft">
              {cpp.ok
                ? (cpp.data.note ?? `${science('kernels')}: ${cpp.data.kernels.join(', ')}`)
                : cpp.error}
            </p>
            <ProvenanceStamp source={CPP_PATH} verified={cpp.ok} method={CPP_PATH} />
          </Card>
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">{PINN_PATH}</p>
              <StatusDot
                state={pinn.ok && pinn.data.available ? 'ok' : 'warn'}
                label={pinn.ok && pinn.data.available ? 'live' : 'unavailable'}
              />
            </div>
            <p className="mt-1 text-xs text-ink-soft">{pinn.ok ? pinn.data.note : pinn.error}</p>
            <ProvenanceStamp source={PINN_PATH} verified={pinn.ok} method={PINN_PATH} />
          </Card>
        </div>
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
            <div className="grid gap-4">
              {models.map((model) => (
                <Card key={model.slug} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">
                        {locale === 'fa' ? model.name_fa : model.name_en}
                      </h3>
                      <p className="mt-1 text-sm text-ink-soft">{model.reference}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusDot
                        state={model.fidelity === 'official' ? 'ok' : 'warn'}
                        label={model.fidelity}
                      />
                      <ProvenanceStamp
                        source={MODELS_PATH}
                        verified={false}
                        method={model.domain}
                        label={model.slug}
                      />
                    </div>
                  </div>
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
