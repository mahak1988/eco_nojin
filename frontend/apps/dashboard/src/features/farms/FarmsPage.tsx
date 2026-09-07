import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getFarms } from '@eco/api';
import { Badge, Button, Card, CardBody, EmptyState, Skeleton } from '@eco/ui';
import { formatNumber } from '@eco/utils';

type FarmRow = {
  id?: number | string;
  name?: string;
  region_name?: string;
  location?: string;
  area_ha?: number;
  area_hectares?: number;
  created_at?: string;
  [key: string]: unknown;
};

export function FarmsPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const farms = useQuery({
    queryKey: ['farms', 'list'],
    queryFn: () => getFarms().listFarmsApiV1FarmsGet(),
    staleTime: 60_000,
  });

  const rows = (farms.data ?? []) as unknown as FarmRow[];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('dashboard.pages.farms.title', 'مزارع')}</h1>
          <p className="text-sm text-ink-muted">
            {t('dashboard.pages.farms.subtitle', 'مزارع ثبت‌شدهٔ شما در پلتفرم — مستقیم از بک‌اند.')}
          </p>
        </div>
        <Badge tone="leaf" variant="soft">{t('dashboard.pages.farms.live', 'متصل به API')}</Badge>
      </header>

      {farms.error ? (
        <EmptyState
          title={t('dashboard.pages.farms.errorTitle', 'دریافت مزارع ناموفق بود')}
          description={(farms.error as Error).message}
          action={
            <Button variant="secondary" onClick={() => void farms.refetch()}>
              {t('common.retry', 'تلاش دوباره')}
            </Button>
          }
        />
      ) : farms.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          title={t('dashboard.pages.farms.emptyTitle', 'هنوز مزرعه‌ای ثبت نشده')}
          description={t('dashboard.pages.farms.emptyBody', 'با ایجاد اولین مزرعه در بک‌اند، همین‌جا نمایش داده می‌شود.')}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((f, idx) => (
            <Card key={f.id ?? idx} className="card-3d transition-all hover:shadow-raised">
              <CardBody className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span aria-hidden="true" className="text-xl">🚜</span>
                  <Badge tone="brand" variant="soft">#{(f.id ?? idx + 1).toString()}</Badge>
                </div>
                <h3 className="text-base font-semibold">{f.name ?? t('dashboard.pages.farms.unnamed', 'بدون نام')}</h3>
                <dl className="grid grid-cols-2 gap-2 border-t border-ink/5 pt-3 text-xs">
                  <div>
                    <dt className="text-ink-muted">{t('dashboard.pages.farms.region', 'منطقه')}</dt>
                    <dd className="font-medium">{f.region_name ?? f.location ?? '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">{t('dashboard.pages.farms.area', 'مساحت')}</dt>
                    <dd className="font-medium">
                      {f.area_ha != null || f.area_hectares != null
                        ? formatNumber((f.area_ha ?? f.area_hectares) as number, { locale, decimals: 0 }) + ' ha'
                        : '—'}
                    </dd>
                  </div>
                  {f.created_at && (
                    <div className="col-span-2">
                      <dt className="text-ink-muted">{t('dashboard.pages.farms.created', 'ایجاد')}</dt>
                      <dd className="font-medium">{new Date(String(f.created_at)).toLocaleDateString(locale)}</dd>
                    </div>
                  )}
                </dl>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
