import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const STATS_PATH = '/api/v1/marketplace/stats';
const MARKETPLACES_PATH = '/api/v1/marketplace/marketplaces';

type MarketplaceStats = {
  total_products: number;
  total_producers: number;
  organic_products: number;
};

type Marketplace = {
  id: string;
  name: string;
  slug: string;
  description: string;
  marketplace_type: string;
};

type Marketplaces = {
  marketplaces: Marketplace[];
};

export const dynamic = 'force-dynamic';

export default async function MarketplaceAccessPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');
  const market = await getTranslations('market');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  const [stats, marketplaces] = await Promise.all([
    apiGet<MarketplaceStats>(STATS_PATH),
    apiGet<Marketplaces>(MARKETPLACES_PATH),
  ]);
  const rows = marketplaces.ok ? marketplaces.data.marketplaces : [];

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={STATS_PATH}
          label={services('title')}
          verified={stats.ok}
          method={STATS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        {stats.ok ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">{stats.data.total_products}</div>
              <p className="mt-1 text-sm text-ink-soft">{market('products')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {stats.data.total_producers}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{market('producers')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {stats.data.organic_products}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{market('organic')}</p>
              <ProvenanceStamp source={STATS_PATH} verified={stats.ok} method={STATS_PATH} />
            </Card>
          </div>
        ) : (
          <Card density="compact">
            <h2 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {stats.error}
            </p>
          </Card>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{MARKETPLACES_PATH}</h2>
        {rows.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">
              {marketplaces.ok ? market('empty') : template('unavailableTitle')}
            </h3>
            <p className="mt-1 text-sm text-ink-soft">
              {marketplaces.ok ? market('empty') : template('unavailableDescription')}
            </p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {marketplaces.ok ? '' : ` · ${marketplaces.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="grid gap-4">
              {rows.map((marketplace) => (
                <Card key={marketplace.id} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">{marketplace.name}</h3>
                      <p className="mt-1 text-sm text-ink-soft">{marketplace.description}</p>
                      <p className="mt-1 text-xs text-ink-soft">{marketplace.marketplace_type}</p>
                    </div>
                    <ProvenanceStamp
                      source={MARKETPLACES_PATH}
                      verified={marketplaces.ok}
                      method={marketplace.slug}
                    />
                  </div>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {MARKETPLACES_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>

      <OwnerFooter />
    </main>
  );
}
