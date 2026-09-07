import { useDashboardFull, useDashboardProjects } from '@eco/api';
import { useTranslation } from 'react-i18next';
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Skeleton, StatCard3D } from '@eco/ui';
import { formatCompact } from '@eco/utils';

type ProjectRow = {
  id?: string;
  name?: string;
  region_name?: string;
  area_ha?: number;
  created_at?: string;
  [key: string]: unknown;
};

export function DashboardHome() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const full = useDashboardFull();
  const projects = useDashboardProjects();

  if (full.error) {
    return (
      <EmptyState
        title={t('dashboard.home.cannotReach', 'اتصال به بک‌اند برقرار نشد')}
        description={(full.error as Error).message}
        action={
          <Button variant="secondary" onClick={() => void full.refetch()}>
            {t('common.retry', 'تلاش دوباره')}
          </Button>
        }
      />
    );
  }

  if (full.isLoading || !full.data) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const data = full.data;

  const kpis: { label: string; value: number; icon: 'database' | 'map' | 'coin' | 'cpu' | 'cloud' | 'sun' | 'satellite' | 'leaf'; color: string; suffix?: string }[] = [
    { label: t('dashboard.home.projects', 'پروژه‌ها'), value: data.projects?.total ?? 0, icon: 'database', color: '#af5f1e' },
    { label: t('dashboard.home.totalArea', 'مساحت کل'), value: data.projects?.total_area_hectares ?? 0, icon: 'map', color: '#0891b2', suffix: 'ha' },
    { label: t('dashboard.home.carbonCredits', 'اعتبار کربن'), value: data.carbon?.total_credits ?? 0, icon: 'coin', color: '#16a34a' },
    { label: t('dashboard.home.activeMotors', 'موتورهای فعال'), value: data.platform?.active_motors ?? 0, icon: 'cpu', color: '#af5f1e' },
    { label: t('dashboard.home.weatherDays', 'روزهای ثبت هوا'), value: data.weather?.days_recorded ?? 0, icon: 'cloud', color: '#0891b2' },
    { label: t('dashboard.home.avgTemp', 'دمای میانگین'), value: data.weather?.avg_temperature_c ?? 0, icon: 'sun', color: '#b45309', suffix: '°C' },
    { label: t('dashboard.home.avgNdvi', 'NDVI میانگین'), value: data.satellite?.avg_ndvi ?? 0, icon: 'satellite', color: '#16a34a' },
    { label: t('dashboard.home.soilProfiles', 'پروفایل خاک'), value: data.soil?.total_profiles ?? 0, icon: 'leaf', color: '#af5f1e' },
  ];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('dashboard.home.title', 'نمای کلی ایستگاه کاری')}</h1>
          <p className="text-sm text-ink-muted">
            {data.timestamp
              ? `${t('dashboard.home.generated', 'تولید‌شده در')} ${new Date(data.timestamp).toLocaleString(locale)}`
              : t('dashboard.home.liveSnapshot', 'نمای زنده')}
          </p>
        </div>
        <Badge tone="success" variant="soft">{t('dashboard.home.live', 'زنده')}</Badge>
      </header>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k, i) => (
          <StatCard3D
            key={k.label}
            index={i}
            label={k.label}
            value={formatCompact(k.value, locale)}
            icon={k.icon}
            color={k.color}
            suffix={k.suffix}
          />
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <h2 className="text-base font-semibold">{t('dashboard.home.recentProjects', 'پروژه‌های اخیر')}</h2>
          </CardHeader>
          <CardBody>
            {projects.isLoading ? (
              <Skeleton className="h-32" />
            ) : (
              <ProjectsTable rows={(projects.data ?? []) as ProjectRow[]} locale={locale} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">{t('dashboard.home.platform', 'پلتفرم')}</h2>
          </CardHeader>
          <CardBody className="grid grid-cols-2 gap-3 text-center text-sm">
            <Tile label={t('dashboard.home.tables', 'جدول‌ها')} value={data.platform?.total_tables ?? 0} locale={locale} />
            <Tile label={t('dashboard.home.services', 'سرویس‌ها')} value={data.platform?.total_services ?? 0} locale={locale} />
            <Tile label={t('dashboard.home.endpoints', 'اندپوینت‌ها')} value={data.platform?.api_endpoints ?? 0} locale={locale} />
            <Tile label={t('dashboard.home.motors', 'موتورها')} value={data.platform?.active_motors ?? 0} locale={locale} />
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

function Tile({ label, value, locale }: { label: string; value: number; locale: string }) {
  return (
    <div className="rounded-md bg-surface-muted p-3">
      <div className="text-lg font-semibold text-brand-700">{formatCompact(value, locale)}</div>
      <div className="text-xs text-ink-muted">{label}</div>
    </div>
  );
}

function ProjectsTable({ rows, locale }: { rows: ProjectRow[]; locale: string }) {
  const { t } = useTranslation();
  if (rows.length === 0) {
    return <p className="text-sm text-ink-muted">{t('dashboard.home.noProjects', 'هنوز پروژه‌ای از بک‌اند گزارش نشده است.')}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-start text-xs uppercase text-ink-muted">
          <tr>
            <th className="py-2 text-start">{t('dashboard.home.name', 'نام')}</th>
            <th className="py-2 text-start">{t('dashboard.home.region', 'منطقه')}</th>
            <th className="py-2 text-start">{t('dashboard.home.area', 'مساحت (هکتار)')}</th>
            <th className="py-2 text-start">{t('dashboard.home.created', 'ایجاد')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ink/5">
          {rows.slice(0, 8).map((row, idx) => (
            <tr key={row.id ?? idx}>
              <td className="py-2">{row.name ?? '—'}</td>
              <td className="py-2">{row.region_name ?? '—'}</td>
              <td className="py-2">{row.area_ha?.toLocaleString(locale) ?? '—'}</td>
              <td className="py-2 text-ink-muted">
                {row.created_at ? new Date(row.created_at).toLocaleDateString(locale) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
