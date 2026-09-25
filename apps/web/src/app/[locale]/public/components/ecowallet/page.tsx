import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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

const TITLES: Record<string, string> = { fa: 'نمایشگاه اکومین', en: 'EcoWallet Demo' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'قابلیت‌های کیف پول دیجیتال',
  en: 'Digital wallet features showcase',
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
      url: `${BASE_URL}/${locale}/public/components/ecowallet`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/ecowallet`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/ecowallet`,
        en: `${BASE_URL}/en/public/components/ecowallet`,
      },
    },
  };
}

export default async function EcoWalletPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [health, earning, redemption] = await Promise.all([
    apiGet<WalletHealth>(HEALTH_PATH),
    apiGet<OptionsPayload>(EARNING_PATH),
    apiGet<OptionsPayload>(REDEMPTION_PATH),
  ]);

  const optionGroups = [
    { path: EARNING_PATH, result: earning },
    { path: REDEMPTION_PATH, result: redemption },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={HEALTH_PATH}
          label={title}
          verified={health.ok}
          method={HEALTH_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {health.ok ? (
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
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        <div className="grid gap-4">
          {optionGroups.map(({ path, result }) => (
            <Card key={path} density="compact">
              <h3 className="font-mono text-sm font-medium text-ink">{path}</h3>
              {result.ok ? (
                result.data.options.length > 0 ? (
                  <div className="mt-3 grid gap-2">
                    {result.data.options.map((option) => (
                      <div
                        key={option.category}
                        className="flex items-center justify-between gap-3 text-sm"
                      >
                        <span className="text-ink">{option.category}</span>
                        <span className="num font-mono text-ink-soft">
                          {option.eco_per_unit ?? option.eco_cost ?? t('unavailable')}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-1 text-sm text-ink-soft">{t('unavailable')}</p>
                )
              ) : (
                <p className="mt-1 text-sm text-ink-soft">
                  {t('unavailable')} · {result.error}
                </p>
              )}
              <div className="mt-3">
                <ProvenanceStamp source={path} verified={result.ok} method={path} />
              </div>
            </Card>
          ))}
        </div>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>
    </main>
  );
}
