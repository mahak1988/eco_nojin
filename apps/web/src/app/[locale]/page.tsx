import { getTranslations, setRequestLocale } from 'next-intl/server';
import { Link } from '@/i18n/navigation';
import { LocaleSwitcher } from '@/components/LocaleSwitcher';
import { apiGet, type PlatformStats } from '@/lib/api/client';
import { getLocaleMeta } from '@/lib/i18n/messages';

// Live backend data: always rendered per request, never prerendered.
export const dynamic = 'force-dynamic';

export default async function CoverPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const meta = await getLocaleMeta(locale);

  const stats = await apiGet<PlatformStats>('/api/v1/platform/stats');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');
  const num = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : nf.format(value);

  return (
    <main className="min-h-dvh">
      <header className="site-header">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-3">
          <img
            src="/brand/platform-logo-transparent.png"
            alt={t('brand.logoAlt')}
            className="h-9 w-auto"
          />
          <LocaleSwitcher current={locale} label={t('cover.languageLabel')} />
        </div>
      </header>

      <section className="contour relative overflow-hidden border-b border-[var(--line)]">
        <div className="mx-auto grid max-w-6xl items-start gap-14 px-5 py-14 lg:grid-cols-12 lg:py-24">
          <div className="lg:col-span-7">
            <span className="chip rise">
              <span
                className="status-dot"
                data-state={stats.ok ? 'ok' : 'warn'}
                aria-hidden="true"
              />
              {t('statusLine.realData')}
            </span>

            <h1 className="display rise rise-2 mt-7 text-balance text-4xl leading-[1.18] text-[var(--ink)] sm:text-5xl lg:text-6xl">
              {t('cover.subtitle')}
            </h1>

            <p className="rise rise-3 mt-6 max-w-xl text-lg text-[var(--ink-soft)]">
              {t('cover.slogan')}
            </p>

            <blockquote className="rise rise-3 mt-8 max-w-xl border-s-2 border-[var(--water)] ps-4 text-sm text-[var(--ink-soft)]">
              {t('cover.quote')}
            </blockquote>

            <div className="rise rise-3 mt-10 flex flex-wrap gap-3">
              <Link href="/home" className="btn btn-primary">
                {t('cover.enterPublic')}
              </Link>
              <Link href="/market" className="btn btn-ghost">
                {t('cover.enterMarketplace')}
              </Link>
            </div>

            {meta.machineTranslated ? (
              <p className="chip mt-8">{t('common.machineTranslatedNotice')}</p>
            ) : null}
          </div>

          <aside className="lg:col-span-5">
            <div className="panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-[var(--ink-soft)]">
                  {t('statusLine.realData')}
                </h2>
                <span
                  className="status-dot"
                  data-state={stats.ok ? 'ok' : 'warn'}
                  aria-hidden="true"
                />
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3">
                <div className="card p-4">
                  <dt className="text-xs text-[var(--ink-soft)]">{t('statusLine.landProfiles')}</dt>
                  <dd className="num mt-1 text-3xl font-semibold text-[var(--ink)]">
                    {stats.ok ? num(stats.data.total_landscapes) : '—'}
                  </dd>
                </div>
                <div className="card p-4">
                  <dt className="text-xs text-[var(--ink-soft)]">
                    {t('statusLine.carbonProjects')}
                  </dt>
                  <dd className="num mt-1 text-3xl font-semibold text-[var(--ink)]">
                    {stats.ok ? num(stats.data.total_projects) : '—'}
                  </dd>
                </div>
              </dl>

              <p className="mt-4 text-xs text-[var(--ink-faint)]">
                {t('statusLine.pilotProvince')}: {t('statusLine.noData')}
              </p>

              {!stats.ok ? (
                <p className="mt-2 text-xs text-[var(--copper)]">
                  /api/v1/platform/stats — {stats.error}
                </p>
              ) : null}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
