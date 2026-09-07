import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getMarketplace } from '@eco/api';
import { Badge, Button, Card, CardBody, EmptyState, Skeleton } from '@eco/ui';
import { formatCurrency, formatNumber } from '@eco/utils';

type ProductRow = {
  id?: number | string;
  name?: string;
  title?: string;
  price?: number;
  unit?: string;
  producer?: string;
  quantity?: number;
  [key: string]: unknown;
};

export function MarketplacePage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const products = useQuery({
    queryKey: ['marketplace', 'products'],
    queryFn: () => getMarketplace().listProductsApiV1MarketplaceProductsGet(),
    staleTime: 60_000,
  });
  const stats = useQuery({
    queryKey: ['marketplace', 'stats'],
    queryFn: () => getMarketplace().marketplaceStatsApiV1MarketplaceStatsGet(),
    staleTime: 60_000,
  });

  const rows = (products.data ?? []) as ProductRow[];
  const statEntries = Object.entries((stats.data ?? {}) as Record<string, unknown>).filter(
    ([, v]) => ['number', 'string', 'boolean'].includes(typeof v),
  );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('dashboard.pages.marketplace.title', 'بازار')}</h1>
          <p className="text-sm text-ink-muted">
            {t('dashboard.pages.marketplace.subtitle', 'محصولات و تولیدکنندگان زنجیرهٔ تأمین شفاف.')}
          </p>
        </div>
        <Badge tone="leaf" variant="soft">{t('dashboard.pages.marketplace.live', 'متصل به API')}</Badge>
      </header>

      {statEntries.length > 0 && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statEntries.slice(0, 4).map(([k, v]) => (
            <Card key={k}>
              <CardBody className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-ink-muted">{humanizeKey(k, t)}</span>
                <span className="text-xl font-semibold text-brand-700">
                  {typeof v === 'number' ? formatNumber(v, { locale }) : String(v)}
                </span>
              </CardBody>
            </Card>
          ))}
        </section>
      )}

      {products.error ? (
        <EmptyState
          title={t('dashboard.pages.marketplace.errorTitle', 'دریافت محصولات ناموفق بود')}
          description={(products.error as Error).message}
          action={
            <Button variant="secondary" onClick={() => void products.refetch()}>
              {t('common.retry', 'تلاش دوباره')}
            </Button>
          }
        />
      ) : products.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          title={t('dashboard.pages.marketplace.emptyTitle', 'محصولی ثبت نشده')}
          description={t('dashboard.pages.marketplace.emptyBody', 'به‌محض ثبت محصول در بک‌اند، اینجا نمایش داده می‌شود.')}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((p, idx) => (
            <Card key={p.id ?? idx} className="card-3d transition-all hover:shadow-raised">
              <CardBody className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span aria-hidden="true" className="text-xl">🛒</span>
                  {p.unit && <Badge tone="sky" variant="soft">{String(p.unit)}</Badge>}
                </div>
                <h3 className="text-base font-semibold">{p.name ?? p.title ?? t('dashboard.pages.marketplace.unnamed', 'بدون نام')}</h3>
                {p.producer && <p className="text-xs text-ink-muted">{String(p.producer)}</p>}
                <div className="mt-auto border-t border-ink/5 pt-3">
                  {typeof p.price === 'number' ? (
                    <span className="text-lg font-bold text-brand-700">{formatCurrency(p.price, 'USD', locale)}</span>
                  ) : (
                    <span className="text-sm text-ink-muted">—</span>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function humanizeKey(key: string, t: ReturnType<typeof useTranslation>['t']): string {
  const map: Record<string, string> = {
    total_products: t('dashboard.pages.marketplace.totalProducts', 'کل محصولات'),
    total_orders: t('dashboard.pages.marketplace.totalOrders', 'کل سفارش‌ها'),
    total_producers: t('dashboard.pages.marketplace.totalProducers', 'تولیدکنندگان'),
    total_revenue: t('dashboard.pages.marketplace.totalRevenue', 'درآمد کل'),
  };
  return map[key] ?? key.replace(/_/g, ' ');
}
