import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getEcowallet } from '@eco/api';
import { Badge, Button, Card, CardBody, EmptyState, Skeleton, StatCard3D } from '@eco/ui';
import { formatNumber } from '@eco/utils';

/** Render whatever the wallet stats endpoint returns — robust to schema drift. */
export function WalletPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const stats = useQuery({
    queryKey: ['ecowallet', 'stats'],
    queryFn: () => getEcowallet().ecowalletStatsApiV1EcowalletStatsGet(),
    staleTime: 60_000,
  });
  const earning = useQuery({
    queryKey: ['ecowallet', 'earning-options'],
    queryFn: () => getEcowallet().getEarningOptionsApiV1EcowalletEarningOptionsGet(),
    staleTime: 300_000,
  });

  const statEntries = Object.entries((stats.data ?? {}) as Record<string, unknown>).filter(
    ([, v]) => ['number', 'string', 'boolean'].includes(typeof v),
  );
  const ICONS = ['coin', 'bolt', 'leaf', 'chart', 'database', 'globe', 'cpu', 'shield'] as const;
  const COLORS = ['#af5f1e', '#0891b2', '#16a34a', '#b45309', '#2563eb', '#16a34a', '#af5f1e', '#0891b2'];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('dashboard.pages.wallet.title', 'کیف پول اکو')}</h1>
          <p className="text-sm text-ink-muted">
            {t('dashboard.pages.wallet.subtitle', 'توکن‌های اکو: کسب از اقدامات سبز، بازخرید و توزیع.')}
          </p>
        </div>
        <Badge tone="brand" variant="soft">{t('dashboard.pages.wallet.live', 'متصل به API')}</Badge>
      </header>

      {stats.error ? (
        <EmptyState
          title={t('dashboard.pages.wallet.errorTitle', 'دریافت آمار کیف پول ناموفق بود')}
          description={(stats.error as Error).message}
          action={
            <Button variant="secondary" onClick={() => void stats.refetch()}>
              {t('common.retry', 'تلاش دوباره')}
            </Button>
          }
        />
      ) : stats.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statEntries.slice(0, 8).map(([k, v], i) => (
            <StatCard3D
              key={k}
              index={i}
              label={humanizeKey(k, t)}
              value={typeof v === 'number' ? formatNumber(v, { locale }) : String(v)}
              icon={ICONS[i % ICONS.length]}
              color={COLORS[i % COLORS.length]}
            />
          ))}
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardBody>
            <h2 className="text-base font-semibold">{t('dashboard.pages.wallet.earningOptions', 'راه‌های کسب توکن')}</h2>
            {earning.isLoading ? (
              <Skeleton className="mt-3 h-24" />
            ) : (
              <OptionsList data={earning.data} emptyText={t('dashboard.pages.wallet.noOptions', 'گزینه‌ای ثبت نشده.')} />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <h2 className="text-base font-semibold">{t('dashboard.pages.wallet.about', 'دربارهٔ توکن اکو')}</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">
              {t(
                'dashboard.pages.wallet.aboutBody',
                'با اجرای اقدامات بازیابی (کاشت، حفاظت، پایش) توکن کسب می‌کنید و می‌توانید در بازار به آن بازخرید یا توزیع کنید. جزئیات کامل در ماژول بلاکچین و اوراکل کربن.',
              )}
            </p>
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

function OptionsList({ data, emptyText }: { data: unknown; emptyText: string }) {
  if (!data) return <p className="mt-2 text-sm text-ink-muted">{emptyText}</p>;
  let items: unknown[] = [];
  if (Array.isArray(data)) items = data;
  else if (typeof data === 'object' && data !== null && Array.isArray((data as Record<string, unknown>)['options']))
    items = (data as Record<string, unknown>)['options'] as unknown[];

  if (items.length === 0) return <p className="mt-2 text-sm text-ink-muted">{emptyText}</p>;

  return (
    <ul className="mt-3 space-y-2 text-sm">
      {items.slice(0, 6).map((item, i) => {
        const obj = item as Record<string, unknown>;
        const title = obj?.['name'] ?? obj?.['title'] ?? obj?.['action'] ?? `#${i + 1}`;
        const desc = obj?.['description'] ?? obj?.['reward'] ?? obj?.['amount'];
        return (
          <li key={i} className="flex items-center justify-between rounded-lg border border-ink/10 bg-surface-muted/60 px-3 py-2">
            <span className="font-medium">{String(title)}</span>
            {desc != null && <span className="text-xs text-ink-muted">{String(desc)}</span>}
          </li>
        );
      })}
    </ul>
  );
}

function humanizeKey(key: string, t: ReturnType<typeof useTranslation>['t']): string {
  const map: Record<string, string> = {
    total_wallets: t('dashboard.pages.wallet.totalWallets', 'کل کیف‌ها'),
    total_tokens: t('dashboard.pages.wallet.totalTokens', 'کل توکن‌ها'),
    tokens_earned: t('dashboard.pages.wallet.tokensEarned', 'توکن کسب‌شده'),
    tokens_redeemed: t('dashboard.pages.wallet.tokensRedeemed', 'توکن بازخریدشده'),
    active_wallets: t('dashboard.pages.wallet.activeWallets', 'کیف‌های فعال'),
  };
  return map[key] ?? key.replace(/_/g, ' ');
}
