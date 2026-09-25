import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const HEALTH_PATH = '/api/v1/health';

const TITLES: Record<string, string> = { fa: 'وضعیت API', en: 'API Status' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'وضعیت زنده گیت‌وی از مسیر واقعی /api/v1/health؛ داده سهمیه و تأخیر هر سرویس منتشر نشده است.',
  en: 'Live gateway state from the real /api/v1/health path; per-service quota and latency are not published.',
};

type GatewayHealth = {
  status: string;
  service: string;
  version: string;
  environment: string;
  checks: Record<string, string>;
  degraded_reasons: string[];
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
      url: `${BASE_URL}/${locale}/developers/status-api`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/developers/status-api`,
      languages: {
        fa: `${BASE_URL}/fa/developers/status-api`,
        en: `${BASE_URL}/en/developers/status-api`,
      },
    },
  };
}

export default async function StatusApiPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('developers');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;

  const health = await apiGet<GatewayHealth>(HEALTH_PATH);
  const gatewayState: DotState = !health.ok
    ? 'down'
    : health.data.status === 'healthy'
      ? 'ok'
      : 'warn';
  const checks = health.ok ? Object.entries(health.data.checks) : [];
  const degraded = health.ok ? health.data.degraded_reasons : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <div className="flex flex-wrap items-center gap-4">
          <ProvenanceStamp
            source={HEALTH_PATH}
            label={title}
            verified={health.ok}
            method={HEALTH_PATH}
          >
            <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          </ProvenanceStamp>
          <StatusDot
            state={gatewayState}
            label={health.ok ? health.data.status : status('unavailable')}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        {health.ok ? (
          <>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <Card density="compact">
                <p className="text-sm text-ink-soft">version</p>
                <p className="num mt-1 font-mono text-ink">{health.data.version}</p>
              </Card>
              <Card density="compact">
                <p className="text-sm text-ink-soft">environment</p>
                <p className="mt-1 font-mono text-ink">{health.data.environment}</p>
              </Card>
            </div>

            {checks.length > 0 && (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-line text-ink-soft">
                      <th className="py-2 pe-4 text-start font-medium">{statusPage('service')}</th>
                      <th className="py-2 text-start font-medium">{statusPage('state')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {checks.map(([name, value]) => (
                      <tr key={name} className="border-b border-line/50">
                        <td className="py-2 pe-4 font-mono text-ink">{name}</td>
                        <td className="py-2 font-mono text-ink-soft">{value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {degraded.length > 0 && (
              <ListBlock title={common('limits')} items={degraded} tone="clay" />
            )}
          </>
        ) : (
          <Card density="cozy" className="mt-6">
            <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {HEALTH_PATH} · {status('unavailable')} · {health.error}
            </p>
          </Card>
        )}

        <div className="mt-6 grid gap-4">
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>

        <p className="mt-6 text-xs text-ink-soft">
          {HEALTH_PATH} · {status('realData')}
        </p>
      </div>
    </main>
  );
}
