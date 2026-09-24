import { getTranslations, setRequestLocale } from 'next-intl/server';
import { Link } from '@/i18n/navigation';
import { SiteNav } from '@/components/SiteNav';
import { OwnerFooter } from '@/components/OwnerFooter';
import {
  apiGet,
  type LandProfile,
  type MarketProducts,
  type PlatformStats,
} from '@/lib/api/client';

// Live backend data: always rendered per request, never prerendered.
export const dynamic = 'force-dynamic';

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const n = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const [stats, lands, products] = await Promise.all([
    apiGet<PlatformStats>('/api/v1/platform/stats'),
    apiGet<LandProfile[]>('/api/v1/platform/landscapes'),
    apiGet<MarketProducts>('/api/v1/marketplace/products'),
  ]);

  const count = (v: number | null | undefined) => (v === null || v === undefined ? '—' : n.format(v));

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <h1 className="display text-4xl font-bold text-ink">{t('home.title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('home.lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-[var(--radius-card)] border border-line bg-surface px-5 py-4">
            <div className="text-sm text-ink-soft">{t('statusLine.landProfiles')}</div>
            <div className="num mt-1 text-3xl font-semibold text-ink">
              {stats.ok ? count(stats.data.total_landscapes) : '—'}
            </div>
          </div>
          <div className="rounded-[var(--radius-card)] border border-line bg-surface px-5 py-4">
            <div className="text-sm text-ink-soft">{t('statusLine.carbonProjects')}</div>
            <div className="num mt-1 text-3xl font-semibold text-ink">
              {stats.ok ? count(stats.data.total_projects) : '—'}
            </div>
          </div>
          <div className="rounded-[var(--radius-card)] border border-line bg-surface px-5 py-4">
            <div className="text-sm text-ink-soft">{t('market.products')}</div>
            <div className="num mt-1 text-3xl font-semibold text-ink">
              {products.ok ? n.format(products.data.products.length) : '—'}
            </div>
          </div>
        </div>
        <p className="mt-2 text-xs text-ink-soft">{t('statusLine.realData')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6">
        <h2 className="text-sm font-semibold text-ink-soft">{t('home.landsTitle')}</h2>
        {lands.ok && lands.data.length > 0 ? (
          <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
            {lands.data.map((lp) => (
              <li key={lp.id} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
                <span className="text-ink">{lp.name}</span>
                <span className="num text-xs text-ink-soft">{lp.created_at ?? '—'}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-xs text-ink-soft">{t('home.landsEmpty')}</p>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink-soft">{t('home.productsTitle')}</h2>
          <Link href="/market" className="text-sm text-water hover:underline">
            {t('home.marketCta')}
          </Link>
        </div>
        {products.ok && products.data.products.length > 0 ? (
          <div className="mt-3 grid gap-4 sm:grid-cols-3">
            {products.data.products.slice(0, 3).map((p) => (
              <article key={p.id} className="rounded-[var(--radius-card)] border border-line bg-surface p-4">
                <div className="text-sm font-semibold text-ink">{p.name}</div>
                <div className="mt-1 text-xs text-ink-soft">{p.producer_name}</div>
                <div className="num mt-3 text-lg text-ink">
                  {n.format(p.price_per_kg)} <span className="text-xs text-ink-soft">/ kg</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-xs text-ink-soft">{t('home.productsEmpty')}</p>
        )}
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6 pb-16">
        <Link href="/hydroma" className="text-sm text-water hover:underline">
          {t('home.scienceCta')}
        </Link>
      </section>

      <OwnerFooter />
    </main>
  );
}
