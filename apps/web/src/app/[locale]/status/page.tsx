import { getTranslations, setRequestLocale } from 'next-intl/server';
import { apiGet, type PlatformHealth, type PlatformStats } from '@/lib/api/client';

// Render the latest registered state for each request.
export const dynamic = 'force-dynamic';

type Row = { key: string; label: string; value: string; ok: boolean };

export default async function StatusPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [health, stats] = await Promise.all([
    apiGet<PlatformHealth>('/api/v1/platform/health'),
    apiGet<PlatformStats>('/api/v1/platform/stats'),
  ]);

  const count = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : String(value);

  const rows: Row[] = [
    {
      key: 'service',
      label: t('statusPage.service'),
      value:
        health.ok && health.data.status === 'operational'
          ? t('statusPage.operational')
          : t('statusLine.unavailable'),
      ok: health.ok && health.data.status === 'operational',
    },
    {
      key: 'science',
      label: t('statusPage.science'),
      value:
        health.ok && health.data.cpp_available
          ? t('statusPage.available')
          : t('statusLine.unavailable'),
      ok: health.ok && health.data.cpp_available,
    },
    {
      key: 'storage',
      label: t('statusPage.storage'),
      value:
        health.ok && health.data.db_reachable
          ? t('statusPage.available')
          : t('statusLine.unavailable'),
      ok: health.ok && health.data.db_reachable,
    },
    {
      key: 'landscapes',
      label: t('statusPage.landscapes'),
      value: stats.ok ? count(stats.data.total_landscapes) : '—',
      ok: stats.ok && stats.data.total_landscapes !== null,
    },
    {
      key: 'projects',
      label: t('statusPage.projects'),
      value: stats.ok ? count(stats.data.total_projects) : '—',
      ok: stats.ok && stats.data.total_projects !== null,
    },
    {
      key: 'active',
      label: t('statusPage.activeProjects'),
      value: stats.ok ? count(stats.data.active_projects) : '—',
      ok: stats.ok && stats.data.active_projects !== null,
    },
  ];

  return (
    <main id="main" className="mx-auto max-w-3xl px-6 py-12">
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
              <td className={`num py-2 ${row.ok ? 'text-forest' : 'text-copper'}`}>{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="mt-10 text-xs text-ink-soft">{t('statusLine.realData')}</p>
      <p className="mt-6 card p-4 text-xs text-ink-soft">{t('statusPage.emptyDbNote')}</p>
    </main>
  );
}
