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

const HEALTH_PATH = '/api/v1/ecowallet/health';
const EARNING_PATH = '/api/v1/ecowallet/earning-options';
const REDEMPTION_PATH = '/api/v1/ecowallet/redemption-options';

type WalletHealth = {
  status: string;
  module: string;
  version: string;
};

type WalletOption = {
  category: string;
  eco_per_unit?: string;
  eco_cost?: string;
  description: string;
};

type OptionsPayload = { options: WalletOption[] };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-ecowallet');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/ecowallet`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/ecowallet'),
      languages: languageAlternates('/public/components/ecowallet'),
    },
  };
}

export default async function EcoWalletPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-components-ecowallet');
  const template = await getTranslations('market.template');
  const title = meta('title');
  const description = meta('description');

  const [health, earning, redemption] = await Promise.all([
    apiGet<WalletHealth>(HEALTH_PATH),
    apiGet<OptionsPayload>(EARNING_PATH),
    apiGet<OptionsPayload>(REDEMPTION_PATH),
  ]);

  const healthState = toDataState(HEALTH_PATH, health, health.ok ? 1 : 0);
  const optionGroups = [
    { path: EARNING_PATH, result: earning },
    { path: REDEMPTION_PATH, result: redemption },
  ].map((group) => ({
    ...group,
    state: toDataState(
      group.path,
      group.result,
      group.result.ok ? group.result.data.options.length : 0,
    ),
  }));
  const readyGroups = optionGroups.filter((group) => group.state.kind === 'ready');
  const readyState = toDataState(
    EARNING_PATH,
    readyGroups.length > 0
      ? { ok: true, data: null, status: 200 }
      : { ok: false, error: '', status: 503 },
    readyGroups.length,
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={HEALTH_PATH}
            label={title}
            verified={health.ok}
            method={HEALTH_PATH}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {healthState.kind === 'ready' && health.ok ? (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">
                {health.data.module} · {health.data.version}
              </p>
              <StatusDot
                state={health.data.status === 'operational' ? 'ok' : 'warn'}
                label={health.data.status}
              />
            </div>
            <div className="mt-2">
              <ProvenanceStamp source={HEALTH_PATH} verified={health.ok} method={HEALTH_PATH} />
            </div>
          </Card>
        ) : (
          <DataStateCard state={healthState} />
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        <div className="grid gap-4">
          {optionGroups.map(({ path, state }) => (
            <div key={path}>
              <h3 className="font-mono text-sm font-medium text-ink">{path}</h3>
              <DataStateCard state={state} />
            </div>
          ))}
        </div>
        <SourceFooter state={readyState} />
      </section>
    </main>
  );
}
