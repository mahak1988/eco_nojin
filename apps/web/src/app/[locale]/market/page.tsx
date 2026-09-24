import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { routing } from '@/i18n/routing';
import { apiGet, type MarketProducts, type MarketStats } from '@/lib/api/client';
import { loadMessages } from '@/lib/i18n/messages';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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
  const messages = (await loadMessages(locale)) as NestedMessages;
  const brandName = messages.brand?.name ?? 'هیدروما نوژین';
  const marketLead = messages.market?.lead ?? 'بازارگاه محصولات تولیدکنندگان با قیمت و موجودی واقعی';

  return {
    title: `بازارگاه · ${brandName}`,
    description: marketLead,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market`,
      title: `بازارگاه · ${brandName}`,
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
    apiGet<MarketProducts>('/api/v1/marketplace/products'),
    apiGet<MarketStats>('/api/v1/marketplace/stats'),
  ]);

  const items = products.ok ? products.data.products : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <h1 className="display text-4xl font-bold text-ink">{t('market.title')}</h1>
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