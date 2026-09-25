import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { apiGet, type PlatformHealth, type PlatformStats } from '@/lib/api/client';
import {
  ADMIN_CONSOLE_ROUTE,
  CONTRACT_LABEL_KEY,
  findCapability,
  LIVE_LABEL_KEY,
  METRIC_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  resolveCapabilityState,
  STATE_LABEL_KEY,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

// Every row is read from the live gateway at request time.
export const dynamic = 'force-dynamic';

type Row = { key: string; label: string; value: string | null; ok: boolean };

const healthCapability = findCapability(ADMIN_CONSOLE_ROUTE, 'platform-health');
const statsCapability = findCapability(ADMIN_CONSOLE_ROUTE, 'platform-stats');

export default async function AdminConsolePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [health, stats] = await Promise.all([
    apiGet<PlatformHealth>('/api/v1/platform/health'),
    apiGet<PlatformStats>('/api/v1/platform/stats'),
  ]);

  const healthState = resolveCapabilityState(healthCapability, health.ok);
  const statsState = resolveCapabilityState(statsCapability, stats.ok);
  const healthData = health.ok ? health.data : null;
  const statsData = stats.ok ? stats.data : null;
  const count = (value: number | null | undefined) =>
    value === null || value === undefined ? null : new Intl.NumberFormat(locale).format(value);

  const rows: Row[] = [
    {
      key: 'service',
      label: t('statusPage.service'),
      value:
        healthState === 'available' && healthData?.status === 'operational'
          ? t(LIVE_LABEL_KEY)
          : t(UNAVAILABLE_LABEL_KEY),
      ok: healthState === 'available' && healthData?.status === 'operational',
    },
    {
      key: 'cpp',
      label: t('statusPage.cpp'),
      value: healthState === 'available' && healthData?.cpp_available ? t(LIVE_LABEL_KEY) : null,
      ok: healthState === 'available' && healthData?.cpp_available === true,
    },
    {
      key: 'database',
      label: t('statusPage.dbReachable'),
      value: healthState === 'available' && healthData?.db_reachable ? t(LIVE_LABEL_KEY) : null,
      ok: healthState === 'available' && healthData?.db_reachable === true,
    },
    {
      key: 'landscapes',
      label: t('statusPage.landscapes'),
      value: statsState === 'available' ? count(statsData?.total_landscapes) : null,
      ok: statsState === 'available' && statsData?.total_landscapes != null,
    },
    {
      key: 'projects',
      label: t('statusPage.projects'),
      value: statsState === 'available' ? count(statsData?.total_projects) : null,
      ok: statsState === 'available' && statsData?.total_projects != null,
    },
    {
      key: 'active',
      label: t('statusPage.activeProjects'),
      value: statsState === 'available' ? count(statsData?.active_projects) : null,
      ok: statsState === 'available' && statsData?.active_projects != null,
    },
  ];

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(ADMIN_CONSOLE_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
      </header>

      <section className="card mt-6 p-5">
        <h2 className="field-label">{t(METRIC_LABEL_KEY)}</h2>
        <table className="mt-3 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-ink-soft">
              <th scope="col" className="py-2 text-start font-medium">
                {t(METRIC_LABEL_KEY)}
              </th>
              <th scope="col" className="py-2 text-start font-medium">
                {t(STATE_LABEL_KEY)}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key} className="border-b border-line">
                <td className="py-2 pe-4 text-ink">{row.label}</td>
                <td className={`num py-2 ${row.ok ? 'text-forest' : 'text-copper'}`}>
                  {row.value ?? t(UNAVAILABLE_LABEL_KEY)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mt-4" aria-labelledby="admin-capabilities">
        <h2 id="admin-capabilities" className="field-label">
          {t(CONTRACT_LABEL_KEY)}
        </h2>
        <ul className="mt-3 space-y-2">
          {ADMIN_CONSOLE_ROUTE.capabilities.map((capability) => {
            const wired = capability.endpoint !== null;
            return (
              <li
                key={capability.id}
                className="card flex flex-wrap items-center justify-between gap-3 p-4"
              >
                <span className="text-sm text-ink">{t(capability.labelKey)}</span>
                <span className="flex flex-wrap items-center gap-3">
                  <span className="num text-xs text-ink-faint">
                    {capability.endpoint ?? t(UNAVAILABLE_LABEL_KEY)}
                  </span>
                  <StatusDot
                    state={wired ? 'ok' : 'down'}
                    label={wired ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
                  />
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </div>
  );
}
