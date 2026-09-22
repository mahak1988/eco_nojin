import { getTranslations, setRequestLocale } from 'next-intl/server';
import {
  apiGet,
  type LandProfile,
  type PlatformHealth,
  type PlatformStats,
} from '@/lib/api/client';

// Live backend data: always rendered per request, never prerendered.
export const dynamic = 'force-dynamic';

type Row = { key: string; label: string; value: string; ok: boolean };

export default async function StatusPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [health, stats, landscapes] = await Promise.all([
    apiGet<PlatformHealth>('/api/v1/platform/health'),
    apiGet<PlatformStats>('/api/v1/platform/stats'),
    apiGet<LandProfile[]>('/api/v1/platform/landscapes'),
  ]);

  const rows: Row[] = [
    {
      key: 'service',
      label: t('statusPage.service'),
      value: health.ok ? health.data.status : `${t('statusLine.unavailable')} (${health.status})`,
      ok: health.ok && health.data.status === 'operational',
    },
    {
      key: 'db',
      label: t('statusPage.dbReachable'),
      value: health.ok ? `${health.data.db_reachable} · ${health.data.db_backend}` : '—',
      ok: health.ok && health.data.db_reachable,
    },
    {
      key: 'cpp',
      label: t('statusPage.cpp'),
      value: health.ok ? String(health.data.cpp_available) : '—',
      ok: health.ok && health.data.cpp_available,
    },
    {
      key: 'landscapes',
      label: t('statusPage.landscapes'),
      value: stats.ok ? String(stats.data.total_landscapes) : '—',
      ok: stats.ok && stats.data.total_landscapes !== null,
    },
    {
      key: 'projects',
      label: t('statusPage.projects'),
      value: stats.ok ? String(stats.data.total_projects) : '—',
      ok: stats.ok && stats.data.total_projects !== null,
    },
    {
      key: 'active',
      label: t('statusPage.activeProjects'),
      value: stats.ok ? String(stats.data.active_projects) : '—',
      ok: stats.ok && stats.data.active_projects !== null,
    },
    {
      key: 'landscapesEndpoint',
      label: '/api/v1/platform/landscapes',
      value: landscapes.ok
        ? `200 OK · ${landscapes.data.length} ${t('statusPage.rows')}`
        : `${landscapes.status} — ${landscapes.error}`,
      ok: landscapes.ok,
    },
  ];

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="display text-4xl font-bold text-ink">{t('statusPage.title')}</h1>
      <p className="mt-3 text-sm text-ink-soft">{t('statusPage.subtitle')}</p>

      <table className="mt-8 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-line text-ink-soft">
            <th className="py-2 text-start font-medium">{t('statusPage.label')}</th>
            <th className="py-2 text-start font-medium">{t('statusPage.state')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className="border-b border-line">
              <td className="py-2 pe-4 text-ink">{row.label}</td>
              <td className={`num py-2 ${row.ok ? 'text-green' : 'text-copper'}`}>{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="mt-10 text-sm font-semibold text-ink-soft">{t('statusPage.landProfileList')}</h2>
      {landscapes.ok && landscapes.data.length > 0 ? (
        <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
          {landscapes.data.map((lp) => (
            <li key={lp.id} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
              <span className="text-ink">{lp.name}</span>
              <span className="num text-xs text-ink-soft">{lp.created_at ?? '—'}</span>
            </li>
          ))}
        </ul>
      ) : landscapes.ok ? (
        <p className="mt-3 text-xs text-ink-soft">{t('statusPage.noLandProfiles')}</p>
      ) : (
        <p className="mt-3 text-xs text-copper">
          {t('statusPage.endpoint')} /api/v1/platform/landscapes — {landscapes.error}
        </p>
      )}

      <p className="mt-6 rounded-[var(--radius-card)] border border-line bg-surface p-4 text-xs text-ink-soft">
        {t('statusPage.emptyDbNote')}
      </p>
    </main>
  );
}
