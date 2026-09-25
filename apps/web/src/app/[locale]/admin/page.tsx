import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminSourceNote,
  AdminUnavailable,
  roleLabel,
} from '@/components/admin/AdminStates';
import {
  type AdminSectionId,
  adminSectionHref,
  findAdminSection,
  getAdminSection,
} from '@/components/admin/admin-sections';
import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { StatusDot } from '@/components/StatusDot';
import type { PlatformHealth, PlatformStats } from '@/lib/api/client';
import { getServiceOverview } from '@/lib/api/health';

// Every row is read from the live gateway at request time.
export const dynamic = 'force-dynamic';

const section = getAdminSection('overview');
const healthCapability = section.capabilities.find((item) => item.id === 'platform-health');
const statsCapability = section.capabilities.find((item) => item.id === 'platform-stats');
const NEXT_SECTIONS: readonly AdminSectionId[] = [
  'system-health',
  'jobs',
  'users',
  'content',
  'feature-flags',
  'security',
];

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
  };
}

type MetricRow = {
  key: string;
  labelKey: string;
  value: string | null;
  numeric: boolean;
  source: string;
};

export default async function AdminOverviewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const session = await readAdminSession();
  const sessionRole = session?.user.role ?? 'regular';
  const token = adminToken(session);
  const [health, stats, services] = await Promise.all([
    adminGet<PlatformHealth>(token, '/api/v1/platform/health'),
    adminGet<PlatformStats>(token, '/api/v1/platform/stats'),
    getServiceOverview(),
  ]);

  const numberFormat = new Intl.NumberFormat(locale);
  const formatCount = (value: number | null | undefined) =>
    typeof value === 'number' ? numberFormat.format(value) : null;

  const healthData = health.ok ? health.data : null;
  const statsData = stats.ok ? stats.data : null;
  const serviceRows = services.ok ? services.data.services : [];
  const summary = services.ok ? services.data.summary : null;
  const lastChecked = serviceRows[0]?.lastCheck;

  const metrics: MetricRow[] = [
    {
      key: 'service',
      labelKey: 'statusPage.service',
      value: healthData?.status === 'operational' ? t('common.live') : null,
      numeric: false,
      source: '/api/v1/platform/health',
    },
    {
      key: 'cpp',
      labelKey: 'statusPage.cpp',
      value: healthData?.cpp_available === true ? t('common.live') : null,
      numeric: false,
      source: '/api/v1/platform/health',
    },
    {
      key: 'database',
      labelKey: 'statusPage.dbReachable',
      value: healthData?.db_reachable === true ? t('common.live') : null,
      numeric: false,
      source: '/api/v1/platform/health',
    },
    {
      key: 'landscapes',
      labelKey: 'statusPage.landscapes',
      value: formatCount(statsData?.total_landscapes),
      numeric: true,
      source: '/api/v1/platform/stats',
    },
    {
      key: 'projects',
      labelKey: 'statusPage.projects',
      value: formatCount(statsData?.total_projects),
      numeric: true,
      source: '/api/v1/platform/stats',
    },
    {
      key: 'active',
      labelKey: 'statusPage.activeProjects',
      value: formatCount(statsData?.active_projects),
      numeric: true,
      source: '/api/v1/platform/stats',
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <div className="card mt-6 p-4">
        <dl className="grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="field-label">{t('platformOverview.itemStatus')}</dt>
            <dd className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink">
              {summary ? (
                <StatusDot
                  state={summary.operational === summary.total ? 'ok' : 'warn'}
                  label={`${summary.operational} / ${summary.total} ${t('common.live')}`}
                />
              ) : (
                <StatusDot state="down" label={t('statusLine.unavailable')} />
              )}
            </dd>
          </div>
          <div>
            <dt className="field-label">{t('market.template.source')}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {lastChecked ?? t('statusLine.unavailable')}
            </dd>
          </div>
          <div>
            <dt className="field-label">{t('auth.session.role')}</dt>
            <dd className="num mt-1 text-sm text-ink">{roleLabel(t, sessionRole)}</dd>
          </div>
        </dl>
      </div>

      <section className="mt-6" aria-labelledby="admin-overview-metrics">
        <h2 id="admin-overview-metrics" className="field-label">
          {t('statusPage.label')}
        </h2>

        <div className="card mt-3 overflow-x-auto">
          <table className="w-full min-w-[30rem] border-collapse text-sm">
            <caption className="px-4 py-3 text-start text-xs text-ink-soft">
              {t('statusPage.subtitle')}
            </caption>
            <thead>
              <tr className="border-y border-line text-ink-soft">
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.label')}
                </th>
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.result')}
                </th>
                <th scope="col" className="px-4 py-2 text-start font-medium">
                  {t('statusPage.endpoint')}
                </th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => (
                <tr key={metric.key} className="border-b border-line last:border-0">
                  <th scope="row" className="px-4 py-2 text-start font-normal text-ink">
                    {t(metric.labelKey)}
                  </th>
                  <td className={`px-4 py-2 ${metric.numeric ? 'num text-end' : ''}`}>
                    {metric.value === null ? (
                      <StatusDot state="down" label={t('statusLine.unavailable')} />
                    ) : (
                      <StatusDot state="ok" label={metric.value} />
                    )}
                  </td>
                  <td className="num px-4 py-2 break-words text-xs text-ink-faint">
                    {metric.source}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6" aria-labelledby="admin-overview-services">
        <h2 id="admin-overview-services" className="field-label">
          {t('platformOverview.itemStatus')}
        </h2>
        {serviceRows.length > 0 ? (
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {serviceRows.map((service) => (
              <li key={service.id} className="card flex items-center justify-between gap-3 p-3">
                <span className="min-w-0">
                  <span className="block truncate text-sm text-ink">{service.name}</span>
                  <span className="num block truncate text-[0.65rem] text-ink-faint">
                    {service.provenance.source}
                  </span>
                </span>
                <span className="flex shrink-0 flex-col items-end gap-1">
                  <StatusDot
                    state={service.status === 'operational' ? 'ok' : 'warn'}
                    label={
                      service.status === 'operational'
                        ? t('common.live')
                        : t('statusLine.unavailable')
                    }
                  />
                  <span className="num text-[0.6rem] text-ink-faint">{service.lastCheck}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-3">
            <AdminUnavailable
              source="API Gateway health endpoints"
              status={services.ok ? 200 : services.status}
              detail={services.ok ? undefined : services.error}
            />
          </div>
        )}
      </section>

      <AdminCapabilityTable id="admin-overview-contract" capabilities={section.capabilities} />

      <section
        className="mt-6 grid gap-4 sm:grid-cols-2"
        aria-label={t('market.template.nextTitle')}
      >
        <div className="card p-5">
          <h2 className="field-label">{t('market.template.contractTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t('market.template.contractDescription')}</p>
          <p className="num mt-3 break-words text-xs text-ink-faint">
            {healthCapability?.endpoint ?? t('statusLine.unavailable')} ·{' '}
            {statsCapability?.endpoint ?? t('statusLine.unavailable')}
          </p>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t('market.template.nextTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t('market.template.nextDescription')}</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {NEXT_SECTIONS.map((id) => {
              const target = findAdminSection(id);
              if (!target) return null;
              return (
                <li key={id}>
                  <Link
                    href={adminSectionHref(locale, target.path)}
                    className="chip hover:bg-[var(--surface-2)]"
                  >
                    {t(target.labelKey)}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      <AdminSourceNote
        source="/api/v1/platform/health · /api/v1/platform/stats"
        ok={health.ok && stats.ok && services.ok}
        observedAt={lastChecked}
      />
    </div>
  );
}
