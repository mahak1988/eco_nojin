import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { type RecoveryLinkItem, RecoveryLinks } from '@/components/system/RecoveryLinks';
import { RefreshStateButton } from '@/components/system/RefreshStateButton';
import { type HealthRow, SystemHealthMatrix } from '@/components/system/SystemHealthMatrix';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet, type CppStatus, type PlatformHealth, type PlatformStats } from '@/lib/api/client';
import { getServiceOverview } from '@/lib/api/health';
import {
  LIVE_LABEL_KEY,
  METRIC_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  RESULT_LABEL_KEY,
  SERVICE_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('statusPage.title'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
    alternates: {
      canonical: `${BASE_URL}/${locale}/system`,
      languages: {
        fa: `${BASE_URL}/fa/system`,
        en: `${BASE_URL}/en/system`,
      },
    },
  };
}

export default async function SystemIndexPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const observedAt = new Date().toISOString();
  const [health, stats, kernels, services] = await Promise.all([
    apiGet<PlatformHealth>('/api/v1/platform/health'),
    apiGet<PlatformStats>('/api/v1/platform/stats'),
    apiGet<CppStatus>('/api/v1/models/cpp-status'),
    getServiceOverview(),
  ]);

  const operational = health.ok && health.data.status === 'operational';
  const serviceRows = services.ok ? services.data.services : [];
  const degraded = serviceRows.filter((service) => service.status !== 'operational');
  const overall: DotState = !health.ok
    ? 'down'
    : !operational
      ? 'warn'
      : degraded.length > 0
        ? 'warn'
        : 'ok';
  const overallLabel = overall === 'ok' ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY);

  const count = (value: number | null | undefined) =>
    value === null || value === undefined
      ? t(UNAVAILABLE_LABEL_KEY)
      : new Intl.NumberFormat(locale).format(value);
  const okOrUnavailable = (reachable: boolean) =>
    reachable ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY);

  const rows: HealthRow[] = [
    {
      id: 'platform',
      label: t(SERVICE_LABEL_KEY),
      token: '/api/v1/platform/health',
      state: health.ok ? (operational ? 'ok' : 'warn') : 'down',
      stateLabel: health.ok && operational ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY),
      result: health.ok ? String(health.data.status) : String(health.status),
    },
    {
      id: 'database',
      label: t('statusPage.dbReachable'),
      token: '/api/v1/platform/health · db_reachable',
      state: health.ok && health.data.db_reachable ? 'ok' : 'down',
      stateLabel: okOrUnavailable(Boolean(health.ok && health.data.db_reachable)),
      result: health.ok ? String(health.data.db_backend) : t(UNAVAILABLE_LABEL_KEY),
    },
    {
      id: 'cpp',
      label: t('statusPage.cpp'),
      token: '/api/v1/models/cpp-status',
      state: kernels.ok && kernels.data.available ? 'ok' : 'down',
      stateLabel: okOrUnavailable(Boolean(kernels.ok && kernels.data.available)),
      result: kernels.ok
        ? `${kernels.data.kernels.length} · ${kernels.data.dll ?? '—'}`
        : t(UNAVAILABLE_LABEL_KEY),
    },
    {
      id: 'landscapes',
      label: t('statusPage.landscapes'),
      token: '/api/v1/platform/stats · total_landscapes',
      state: stats.ok && stats.data.total_landscapes !== null ? 'ok' : 'down',
      stateLabel: stats.ok ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY),
      result: count(stats.ok ? stats.data.total_landscapes : null),
    },
    {
      id: 'projects',
      label: t('statusPage.projects'),
      token: '/api/v1/platform/stats · total_projects',
      state: stats.ok && stats.data.total_projects !== null ? 'ok' : 'down',
      stateLabel: stats.ok ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY),
      result: count(stats.ok ? stats.data.total_projects : null),
    },
    {
      id: 'active',
      label: t('statusPage.activeProjects'),
      token: '/api/v1/platform/stats · active_projects',
      state: stats.ok && stats.data.active_projects !== null ? 'ok' : 'down',
      stateLabel: stats.ok ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY),
      result: count(stats.ok ? stats.data.active_projects : null),
    },
    ...serviceRows.map(
      (service): HealthRow => ({
        id: `service-${service.id}`,
        label: service.name,
        token: `/api/v1/${service.id}/health`,
        state: service.status === 'operational' ? 'ok' : 'warn',
        stateLabel: service.status === 'operational' ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY),
        result: service.lastCheck.slice(11, 19),
      }),
    ),
  ];

  const recovery: RecoveryLinkItem[] = [
    {
      href: '/status',
      label: t('statusPage.title'),
      detail: t('statusPage.subtitle'),
      token: '/status',
    },
    { href: '/system/pwa-update', label: t('public.channels.webPwa'), token: '/system/pwa-update' },
    {
      href: '/system/locale-fallback',
      label: t('cover.languageLabel'),
      token: '/system/locale-fallback',
    },
    {
      href: '/system/webgpu-fallback',
      label: t('statusPage.cpp'),
      token: '/system/webgpu-fallback',
    },
    {
      href: '/offline',
      label: t('offline.title'),
      detail: t('offline.description'),
      token: '/offline',
    },
    { href: '/help', label: t('public.channels.title'), token: '/help' },
    { href: '/accessibility', label: t('accessibility.title'), detail: t('accessibility.lead') },
    { href: '/trust', label: t('trust.title'), detail: t('trust.lead') },
  ];

  return (
    <main id="main" className="mx-auto max-w-5xl px-6 py-12">
      <header>
        <span className="chip num font-mono">system</span>
        <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">
          {t('statusPage.title')}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <StatusDot state={overall} label={overallLabel} />
          <span className="num text-xs text-ink-faint">
            <time dateTime={observedAt}>{observedAt.slice(11, 19)}</time> · {t(RESULT_LABEL_KEY)}
          </span>
          <RefreshStateButton label={t('common.retry')} />
        </div>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="system-health">
        <h2 id="system-health" className="field-label">
          {t(METRIC_LABEL_KEY)}
        </h2>
        <div className="mt-3">
          <SystemHealthMatrix
            rows={rows}
            labels={{
              metric: t(METRIC_LABEL_KEY),
              state: t(STATE_LABEL_KEY),
              result: t(RESULT_LABEL_KEY),
              caption: t(SERVICE_LABEL_KEY),
            }}
            emptyLabel={t(UNAVAILABLE_LABEL_KEY)}
          />
        </div>
      </section>

      <div className="mt-6">
        <RecoveryLinks
          links={recovery}
          heading={t('common.nextLabel')}
          headingId="system-recovery"
          viewLabel={t('common.view')}
        />
      </div>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </main>
  );
}
