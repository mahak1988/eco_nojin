import { getTranslations, setRequestLocale } from 'next-intl/server';
import { Link } from '@/i18n/navigation';
import { LocaleSwitcher } from '@/components/LocaleSwitcher';
import { apiGet, type PlatformStats } from '@/lib/api/client';
import { getLocaleMeta } from '@/lib/i18n/messages';

// Live backend data: always rendered per request, never prerendered.
export const dynamic = 'force-dynamic';

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-[var(--radius-card)] border border-line bg-surface px-5 py-4">
      <div className="text-sm text-ink-soft">{label}</div>
      <div className="num mt-1 text-3xl font-semibold text-ink">{value}</div>
      {note ? <div className="mt-1 text-xs text-ink-soft">{note}</div> : null}
    </div>
  );
}

export default async function CoverPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const meta = await getLocaleMeta(locale);

  const stats = await apiGet<PlatformStats>('/api/v1/platform/stats');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');
  const num = (v: number | null | undefined) =>
    v === null || v === undefined ? '—' : nf.format(v);

  return (
    <main className="min-h-dvh">
      <div className="contour">
        <header className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <span className="font-semibold tracking-tight text-ink">{t('brand.name')}</span>
          <LocaleSwitcher current={locale} label={t('cover.languageLabel')} />
        </header>

        <section className="mx-auto max-w-5xl px-6 pb-16 pt-10">
          <h1 className="display text-5xl font-bold leading-tight text-ink sm:text-6xl">
            {t('brand.name')}
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-ink-soft">{t('cover.subtitle')}</p>
          <p className="mt-6 max-w-2xl text-base text-ink">{t('cover.slogan')}</p>
          <blockquote className="mt-8 max-w-2xl border-s-2 border-water/60 ps-4 text-sm text-ink-soft">
            {t('cover.quote')}
          </blockquote>
          {meta.machineTranslated ? (
            <p className="mt-4 inline-block rounded-full border border-line px-3 py-1 text-xs text-ink-soft">
              {t('common.machineTranslatedNotice')}
            </p>
          ) : null}

          <div className="mt-10 flex flex-wrap gap-3">
            <Link
              href="/status"
              className="rounded-[var(--radius-card)] bg-water px-5 py-3 text-sm font-semibold text-white hover:opacity-90"
            >
              {t('cover.enterPublic')}
            </Link>
            <span className="rounded-[var(--radius-card)] border border-line px-5 py-3 text-sm text-ink-soft">
              {t('cover.enterMarketplace')} · {t('cover.comingSoon')}
            </span>
          </div>
        </section>
      </div>

      <section className="mx-auto max-w-5xl px-6 py-10">
        <h2 className="text-sm font-semibold text-ink-soft">{t('statusLine.realData')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <Stat
            label={t('statusLine.landProfiles')}
            value={stats.ok ? num(stats.data.total_landscapes) : '—'}
            note={stats.ok ? t('statusLine.realData') : t('statusLine.unavailable')}
          />
          <Stat
            label={t('statusLine.carbonProjects')}
            value={stats.ok ? num(stats.data.total_projects) : '—'}
            note={stats.ok ? t('statusLine.realData') : t('statusLine.unavailable')}
          />
          <Stat label={t('statusLine.pilotProvince')} value={t('statusLine.noData')} />
        </div>
        {!stats.ok ? (
          <p className="mt-3 text-xs text-copper">
            /api/v1/platform/stats — {stats.error}
          </p>
        ) : null}
      </section>
    </main>
  );
}
