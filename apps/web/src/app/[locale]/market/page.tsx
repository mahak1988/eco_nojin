import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { SITE_URL as BASE_URL } from '@/config/site';
import { routing } from '@/i18n/routing';
import { apiGet, type MarketProducts, type MarketStats } from '@/lib/api/client';
import { loadMessages } from '@/lib/i18n/messages';

const PRODUCTS_SOURCE = '/api/v1/marketplace/products';
const STATS_SOURCE = '/api/v1/marketplace/stats';

type NestedMessages = {
  brand?: { name?: string };
  market?: { lead?: string };
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const messages = (await loadMessages(locale)) as NestedMessages;
  const brandName = messages.brand?.name ?? '';
  const marketLead = messages.market?.lead ?? '';
  const title = marketLead ? `${brandName} · ${marketLead}` : brandName;

  return {
    title,
    description: marketLead,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market`,
      title,
      description: marketLead,
      images: [
        {
          url: `${BASE_URL}/og-market.png`,
          width: 1200,
          height: 630,
          alt: 'Eco Nojin Marketplace',
        },
      ],
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/market`,
      languages: Object.fromEntries(
        routing.locales.map((loc) => [loc, `${BASE_URL}/${loc}/market`]),
      ),
    },
  };
}

export const dynamic = 'force-dynamic';

export default async function MarketPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const n = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const [products, stats] = await Promise.all([
    apiGet<MarketProducts>(PRODUCTS_SOURCE),
    apiGet<MarketStats>(STATS_SOURCE),
  ]);

  const items = products.ok ? products.data.products : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display flex-1 text-4xl font-bold text-ink">{t('market.title')}</h1>
          <ProvenanceStamp
            source={PRODUCTS_SOURCE}
            label={t('market.lead')}
            method={products.ok ? t('statusLine.realData') : undefined}
          />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('market.lead')}</p>
      </section>

      {stats.ok ? (
        <section className="mx-auto max-w-5xl px-6 py-2">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="card px-5 py-4">
              <div className="text-sm text-ink-soft">{t('market.products')}</div>
              <div className="num mt-1 text-2xl font-semibold text-ink">
                {n.format(stats.data.total_products)}
              </div>
            </div>
            <div className="card px-5 py-4">
              <div className="text-sm text-ink-soft">{t('market.producers')}</div>
              <div className="num mt-1 text-2xl font-semibold text-ink">
                {n.format(stats.data.total_producers)}
              </div>
            </div>
            <div className="card px-5 py-4">
              <div className="text-sm text-ink-soft">{t('market.organic')}</div>
              <div className="num mt-1 text-2xl font-semibold text-ink">
                {n.format(stats.data.organic_products)}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      <section className="mx-auto max-w-5xl px-6 py-6 pb-16">
        <h2 className="text-sm font-semibold text-ink-soft">{t('market.products')}</h2>
        {items.length > 0 ? (
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            {items.map((p) => (
              <article key={p.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{p.name}</div>
                    <div className="mt-1 text-xs text-ink-soft">{p.producer_name}</div>
                  </div>
                  {p.organic_certified ? (
                    <span className="rounded-full border border-line px-2 py-0.5 text-[10px] text-forest">
                      {t('market.organicBadge')}
                    </span>
                  ) : null}
                </div>
                <p className="mt-3 text-xs text-ink-soft">{p.description}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="num text-lg text-ink">
                    {n.format(p.price_per_kg)} <span className="text-xs text-ink-soft">/ kg</span>
                  </span>
                  <span className="num text-xs text-ink-soft">
                    {n.format(p.quantity_available_kg)} kg
                  </span>
                </div>
                <Link
                  href={`/${locale}/market/product/${p.id}`}
                  className="mt-3 inline-block text-xs text-forest underline"
                >
                  {t('common.view')}
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-xs text-ink-soft">
            {products.ok ? t('market.empty') : `${t('statusLine.unavailable')} — ${products.error}`}
          </p>
        )}
      </section>
    </main>
  );
}
