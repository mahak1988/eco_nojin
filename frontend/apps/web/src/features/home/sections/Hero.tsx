import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { Badge } from '@eco/ui';
import { Reveal } from '@eco/ui';
import { AreaChart, GaugeChart } from '@eco/charts';
import { AnimatedCounter } from '@eco/ui';
import { DASHBOARD_URL } from '@eco/config';
import { cn } from '@eco/utils';

const FADE_STATS: { value: number; suffix: string; labelKey: string; fallback: string; tone: 'brand' | 'sky' | 'leaf' }[] = [
  { value: 26, suffix: '٪', labelKey: 'finance.irr', fallback: 'بهره‌وری آبیاری', tone: 'brand' },
  { value: 2.8, suffix: '×', labelKey: 'finance.bc', fallback: 'نسبت فایده به هزینه', tone: 'sky' },
  { value: 318, suffix: '', labelKey: 'nav.models', fallback: 'مدل علمی', tone: 'leaf' },
  { value: 4.2, suffix: ' سال', labelKey: 'finance.payback', fallback: 'بازگشت سرمایه', tone: 'brand' },
];

const TONE_TEXT: Record<'brand' | 'sky' | 'leaf', string> = {
  brand: 'text-brand-700 dark:text-brand-300',
  sky: 'text-sky-700 dark:text-sky-300',
  leaf: 'text-leaf-700 dark:text-leaf-300',
};

export function Hero() {
  const { t } = useTranslation();

  return (
    <section className="relative isolate overflow-hidden bg-surface-inverse text-ink-inverse">
      {/* Soft product glow — the only decoration, like Apple keynote pages */}
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 -z-10 flex justify-center">
        <div className="h-[420px] w-[720px] rounded-full bg-gradient-brand opacity-20 blur-[160px]" />
      </div>

      <div className="mx-auto w-full max-w-content px-4 pt-24 pb-28 sm:px-6 lg:pt-32 lg:pb-40">
        <div className="mx-auto max-w-3xl text-center">
          <Reveal>
            <p className="text-sm font-medium text-ink-subtle">{t('app.tagline')}</p>
          </Reveal>

          <Reveal delay={80}>
            <h1 className="mt-4 text-balance text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
              {t('home.heroTitle')}
            </h1>
          </Reveal>

          <Reveal delay={160}>
            <p className="mx-auto mt-6 max-w-2xl text-balance text-lg leading-relaxed text-ink-subtle md:text-xl">
              {t('home.heroSubtitle')}
            </p>
          </Reveal>

          <Reveal delay={240}>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-6">
              <a
                href={DASHBOARD_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-12 items-center rounded-full bg-gradient-brand px-7 text-sm font-medium text-white transition-all hover:opacity-90 focus-visible:outline-none"
              >
                {t('home.openDashboard')}
              </a>
              <Link to="/models" className="link-apple inline-flex items-center gap-1 text-base">
                {t('nav.models')}
                <span aria-hidden className="rtl-flip">‹</span>
              </Link>
            </div>
          </Reveal>

          <Reveal delay={300}>
            <p className="mt-6 text-xs text-ink-subtle">
              {t('home.noSignup')} · {t('home.openSource')}
            </p>
          </Reveal>
        </div>

        {/* Live snapshot (demo data) — white card on black, like an Apple product tile */}
        <Reveal delay={380} className="mt-20 lg:mt-24">
          <div className="relative mx-auto max-w-4xl">
            <div className="glass overflow-hidden p-6 shadow-elevated md:p-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-leaf-500" />
                  {t('home.liveSnapshot')}
                </div>
                <Badge tone="info" variant="soft" className="text-[10px]">v2.0</Badge>
              </div>

              <h3 className="mt-3 text-xl font-semibold tracking-tight text-ink">{t('home.platformTitle')}</h3>

              <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
                {FADE_STATS.map((s) => (
                  <SnapshotStat key={s.labelKey} {...s} />
                ))}
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-ink/5 bg-surface p-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-medium text-ink">{t('home.socDemo', 'مسیر کربن آلی خاک (نمونه)')}</span>
                    <span className="text-ink-muted">+ 1.42 tC/ha/yr</span>
                  </div>
                  <AreaChart
                    height={140}
                    categories={['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']}
                    series={[
                      {
                        name: 'SOC',
                        data: [42, 42.5, 43, 43.2, 43.8, 44.1, 44.5, 44.8, 45.2, 45.5, 45.8, 46],
                      },
                    ]}
                  />
                </div>
                <div className="rounded-2xl border border-ink/5 bg-surface p-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-medium text-ink">{t('finance.irr')}</span>
                    <span className="font-medium text-ink">26٪</span>
                  </div>
                  <GaugeChart value={26} min={0} max={100} unit="٪" height={140} />
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function SnapshotStat({
  value,
  suffix,
  labelKey,
  fallback,
  tone,
}: {
  value: number;
  suffix: string;
  labelKey: string;
  fallback: string;
  tone: 'brand' | 'sky' | 'leaf';
}) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const decimals = Number.isInteger(value) ? 0 : 1;
  return (
    <div className="rounded-2xl border border-ink/5 bg-surface p-4">
      <div className={cn('text-2xl font-bold tracking-tight', TONE_TEXT[tone])}>
        <AnimatedCounter
          from={0}
          to={value}
          duration={1600}
          formatter={(v) => `${v.toLocaleString(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`}
        />
      </div>
      <div className="mt-1 text-xs text-ink-muted">{t(labelKey, fallback)}</div>
    </div>
  );
}
