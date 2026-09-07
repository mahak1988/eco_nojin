import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { useTranslation } from 'react-i18next';
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
  const reduceMotion = useMemo(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  // Stable pseudo-random particle positions (never re-rolled on re-render).
  const particles = useMemo(
    () =>
      Array.from({ length: 12 }, (_, i) => ({
        id: i,
        top: 15 + ((i * 37) % 70),
        left: 5 + ((i * 61) % 90),
        duration: 4 + ((i * 13) % 60) / 10,
        delay: ((i * 29) % 50) / 10,
      })),
    [],
  );

  return (
    <section className="relative isolate overflow-hidden">
      {/* Background layers */}
      <div className="absolute inset-0 -z-20 bg-gradient-to-b from-sky-50 via-brand-50/60 to-surface dark:from-slate-950 dark:via-slate-900 dark:to-slate-950" />

      {/* Mesh orbs */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-24 start-10 h-[500px] w-[500px] rounded-full bg-sky-300/20 blur-[120px] dark:bg-sky-700/15" />
        <div className="absolute top-1/3 end-10 h-[400px] w-[400px] rounded-full bg-brand-300/20 blur-[100px] dark:bg-brand-700/15" />
        <div className="absolute -bottom-20 start-1/3 h-[350px] w-[350px] rounded-full bg-leaf-300/20 blur-[100px] dark:bg-leaf-700/10" />
      </div>

      {/* Blurred globe background */}
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 -z-10 flex justify-center">
        <svg
          viewBox="0 0 400 400"
          className="h-[600px] w-[600px] max-w-none opacity-[0.08] dark:opacity-[0.12]"
          style={{ filter: 'blur(60px)' }}
        >
          <defs>
            <radialGradient id="globe-fade" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.6" />
              <stop offset="60%" stopColor="currentColor" stopOpacity="0.3" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </radialGradient>
          </defs>
          <g fill="none" stroke="currentColor" strokeWidth="1.2" className="text-brand-600 dark:text-brand-400">
            <circle cx="200" cy="200" r="150" />
            <circle cx="200" cy="200" r="120" />
            <circle cx="200" cy="200" r="90" />
            <circle cx="200" cy="200" r="60" />
            <ellipse cx="200" cy="200" rx="150" ry="60" />
            <ellipse cx="200" cy="200" rx="150" ry="30" />
            <ellipse cx="200" cy="200" rx="120" ry="45" />
            <ellipse cx="200" cy="200" rx="90" ry="30" />
            <line x1="50" y1="200" x2="350" y2="200" />
            <line x1="200" y1="50" x2="200" y2="350" />
          </g>
          <g fill="currentColor" className="text-brand-500 dark:text-brand-300" opacity="0.4">
            <circle cx="160" cy="140" r="2.5" /><circle cx="220" cy="120" r="2" />
            <circle cx="180" cy="180" r="2.5" /><circle cx="240" cy="160" r="2" />
            <circle cx="150" cy="220" r="2" /><circle cx="210" cy="240" r="2.5" />
            <circle cx="260" cy="200" r="2" /><circle cx="190" cy="270" r="2" />
            <circle cx="230" cy="280" r="2.5" /><circle cx="170" cy="300" r="2" />
            <circle cx="140" cy="170" r="1.5" /><circle cx="250" cy="250" r="1.5" />
            <circle cx="270" cy="140" r="2" /><circle cx="130" cy="260" r="2" />
          </g>
        </svg>
      </div>

      {/* Landscape silhouette */}
      <div aria-hidden className="absolute inset-x-0 bottom-0 -z-10 h-64 bg-gradient-to-t from-surface via-surface/80 to-transparent" />
      <svg aria-hidden className="absolute inset-x-0 bottom-0 -z-10 h-48 w-full text-surface-muted/60 dark:text-slate-900/60" viewBox="0 0 1440 320" preserveAspectRatio="none">
        <path fill="currentColor" d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,224C672,245,768,267,864,261.3C960,256,1056,224,1152,197.3C1248,171,1344,149,1392,138.7L1440,128L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z" />
        <path fill="currentColor" className="opacity-40" d="M0,256L60,240C120,224,240,192,360,192C480,192,600,224,720,234.7C840,245,960,235,1080,213.3C1200,192,1320,160,1380,144L1440,128L1440,320L1380,320C1320,320,1200,320,1080,320C960,320,840,320,720,320C600,320,480,320,360,320C240,320,120,320,60,320L0,320Z" />
      </svg>

      {/* Floating particles */}
      {!reduceMotion && (
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          {particles.map((p) => (
            <span
              key={p.id}
              className="absolute inline-block h-1.5 w-1.5 rounded-full bg-ink/10 dark:bg-white/10"
              style={{
                top: `${p.top}%`,
                left: `${p.left}%`,
                animation: `float ${p.duration}s ease-in-out infinite`,
                animationDelay: `${p.delay}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Content */}
      <div className="mx-auto w-full max-w-content px-4 pt-20 pb-28 sm:px-6 lg:px-8 lg:pt-28 lg:pb-36">
        <div className="mx-auto max-w-4xl text-center">
          <Reveal>
            <Badge tone="brand" variant="soft" className="mx-auto gap-2 px-4 py-1.5 text-xs">
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-brand-500" />
              {t('app.tagline')}
            </Badge>
          </Reveal>

          <Reveal delay={100}>
            <h1 className="mt-8 text-balance text-5xl font-bold leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-7xl">
              <span className="text-gradient-brand">{t('home.heroTitle')}</span>
            </h1>
          </Reveal>

          <Reveal delay={200}>
            <p className="mx-auto mt-7 max-w-2xl text-balance text-lg leading-relaxed text-ink-muted md:text-xl">
              {t('home.heroSubtitle')}
            </p>
          </Reveal>

          <Reveal delay={280}>
            <p className="mx-auto mt-4 max-w-xl text-pretty text-sm leading-relaxed text-ink-muted">
              {t('home.subtitle')}
            </p>
          </Reveal>

          <Reveal delay={360}>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <a
                href={DASHBOARD_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-12 items-center gap-2 rounded-full bg-ink px-7 text-sm font-semibold text-ink-inverse shadow-raised transition-all hover:-translate-y-0.5 hover:shadow-elevated focus-visible:shadow-glow focus-visible:outline-none"
              >
                {t('home.openDashboard')}
                <span aria-hidden className="rtl-flip">→</span>
              </a>
              <Link
                to="/models"
                className="inline-flex h-12 items-center gap-2 rounded-full border border-ink/15 bg-surface-raised/70 px-7 text-sm font-semibold text-ink backdrop-blur transition-colors hover:bg-surface-raised"
              >
                {t('nav.models')}
              </Link>
            </div>
          </Reveal>

          <Reveal delay={420}>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-ink-muted">
              <div className="flex items-center gap-1.5">
                <CheckIcon /> {t('home.noSignup')}
              </div>
              <div className="hidden h-3 w-px bg-ink/15 md:block" />
              <div className="flex items-center gap-1.5">
                <CheckIcon /> {t('home.openSource')}
              </div>
            </div>
          </Reveal>
        </div>

        {/* Live snapshot preview (demo data) */}
        <Reveal delay={500} className="mt-16 lg:mt-20">
          <div className="relative mx-auto max-w-4xl">
            <div className="glass card-3d rounded-3xl p-6 shadow-elevated md:p-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-ink-muted">
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
                <div className="rounded-2xl border border-ink/10 bg-surface-muted/60 p-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-medium">{t('home.socDemo', 'مسیر کربن آلی خاک (نمونه)')}</span>
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
                <div className="rounded-2xl border border-ink/10 bg-surface-muted/60 p-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-medium">{t('finance.irr')}</span>
                    <span className="text-brand-700 dark:text-brand-300">26٪</span>
                  </div>
                  <GaugeChart value={26} min={0} max={100} unit="٪" height={140} />
                </div>
              </div>
            </div>
            <div aria-hidden className="absolute -bottom-10 -end-10 -z-10 h-44 w-44 rounded-full bg-gradient-brand opacity-15 blur-3xl" />
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
    <div className="rounded-xl border border-ink/10 bg-surface-muted p-4">
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

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M4 12l5 5L20 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// Re-exported for convenience so section files stay dependency-light.
export { Reveal };
