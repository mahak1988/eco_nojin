import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import {
  apiGet,
  type LandProfile,
  type PlatformHealth,
  type PlatformStats,
} from '@/lib/api/client';
import { getServiceOverview } from '@/lib/api/health';

export const dynamic = 'force-dynamic';

type Row = { key: string; label: string; value: string; ok: boolean };

export default async function StatusPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');

  const [health, stats, services, landscapes] = await Promise.all([
    apiGet<PlatformHealth>('/api/v1/platform/health'),
    apiGet<PlatformStats>('/api/v1/platform/stats'),
    getServiceOverview(),
    apiGet<LandProfile[]>('/api/v1/platform/landscapes'),
  ]);

  const liveLabel = common('live');
  const downLabel = statusLine('unavailable');
  const count = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : String(value);

  const rows: Row[] = [
    {
      key: 'service',
      label: statusPage('service'),
      value: health.ok && health.data.status === 'operational' ? liveLabel : downLabel,
      ok: health.ok && health.data.status === 'operational',
    },
    {
      key: 'cpp',
      label: statusPage('cpp'),
      value: health.ok && health.data.cpp_available ? liveLabel : downLabel,
      ok: health.ok && health.data.cpp_available,
    },
    {
      key: 'storage',
      label: statusPage('dbReachable'),
      value: health.ok && health.data.db_reachable ? liveLabel : downLabel,
      ok: health.ok && health.data.db_reachable,
    },
    {
      key: 'landscapes',
      label: statusPage('landscapes'),
      value: stats.ok ? count(stats.data.total_landscapes) : '—',
      ok: stats.ok && stats.data.total_landscapes !== null,
    },
    {
      key: 'projects',
      label: statusPage('projects'),
      value: stats.ok ? count(stats.data.total_projects) : '—',
      ok: stats.ok && stats.data.total_projects !== null,
    },
    {
      key: 'active',
      label: statusPage('activeProjects'),
      value: stats.ok ? count(stats.data.active_projects) : '—',
      ok: stats.ok && stats.data.active_projects !== null,
    },
  ];

  const serviceRows = services.ok ? services.data.services : [];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="display text-4xl font-bold text-ink">{statusPage('title')}</h1>
        <p className="mt-3 text-sm text-ink-soft">{statusPage('subtitle')}</p>

        <div className="mt-6">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-ink-soft">
                <th className="py-2 text-start font-medium">{statusPage('label')}</th>
                <th className="py-2 text-start font-medium">{statusPage('state')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-line">
                  <td className="py-2 pe-4 text-ink">{row.label}</td>
                  <td className={`num py-2 ${row.ok ? 'text-forest' : 'text-copper'}`}>
                    {row.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <section className="mt-10" aria-labelledby="service-health">
          <h2 id="service-health" className="field-label">
            {statusPage('service')}
          </h2>
          {serviceRows.length > 0 ? (
            <table className="mt-3 w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                  <th className="py-2 text-start font-medium">{statusPage('state')}</th>
                </tr>
              </thead>
              <tbody>
                {serviceRows.map((service) => {
                  const ok = service.status === 'operational';
                  return (
                    <tr key={service.id} className="border-b border-line">
                      <td className="py-2 pe-4 text-ink">{service.name}</td>
                      <td className={`py-2 ${ok ? 'text-forest' : 'text-copper'}`}>
                        <StatusDot
                          state={(ok ? 'ok' : 'warn') satisfies DotState}
                          label={ok ? liveLabel : downLabel}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p className="mt-3 text-sm text-copper">{downLabel}</p>
          )}
        </section>

        <section className="mt-10" aria-labelledby="land-profiles">
          <h2 id="land-profiles" className="field-label">
            {statusPage('landProfileList')}
          </h2>
          {landscapes.ok && landscapes.data.length > 0 ? (
            <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
              {landscapes.data.map((profile) => (
                <li
                  key={profile.id}
                  className="flex items-center justify-between gap-4 px-4 py-3 text-sm"
                >
                  <span className="text-ink">{profile.name}</span>
                  <span className="num text-xs text-ink-soft">
                    {profile.created_at ? profile.created_at.slice(0, 10) : '—'}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-ink-soft">
              {landscapes.ok ? statusPage('noLandProfiles') : downLabel}
            </p>
          )}
        </section>

        <p className="mt-10 text-xs text-ink-soft">{statusLine('realData')}</p>
        <p className="mt-6 card p-4 text-xs text-ink-soft">{statusPage('emptyDbNote')}</p>
      </div>
    </main>
  );
}
