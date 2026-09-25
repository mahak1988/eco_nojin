import type { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

export const metadata: Metadata = {
  title: 'Living Terrain — Design System 2026',
  description:
    'Team-only living reference for Design System «زمینِ زنده» — tokens, typography, motion and signature visuals.',
  robots: { index: false, follow: false },
};

/**
 * Living design-system reference (Design System §4.7).
 * All labels are locale-neutral token identifiers / code, so no translated
 * copy is hard-coded here; product pages read from `messages/<locale>/*`.
 */
const palette: { token: string; value: string }[] = [
  { token: '--canvas', value: 'light-dark(oklch(0.965 0.008 100), oklch(0.17 0.015 210))' },
  { token: '--surface', value: 'light-dark(oklch(0.995 0.004 100), oklch(0.21 0.017 210))' },
  { token: '--ink', value: 'light-dark(oklch(0.26 0.015 210), oklch(0.93 0.012 120))' },
  { token: '--water', value: 'light-dark(oklch(0.55 0.11 235), oklch(0.72 0.12 220))' },
  { token: '--forest', value: 'light-dark(oklch(0.52 0.12 152), oklch(0.7 0.15 155))' },
  { token: '--moss', value: 'light-dark(oklch(0.5 0.09 130), oklch(0.62 0.1 130))' },
  { token: '--soil', value: 'light-dark(oklch(0.45 0.06 70), oklch(0.66 0.09 75))' },
  { token: '--copper', value: 'light-dark(oklch(0.58 0.13 45), oklch(0.72 0.14 55))' },
  { token: '--clay', value: 'light-dark(oklch(0.55 0.12 35), oklch(0.68 0.13 35))' },
  { token: '--sky', value: 'light-dark(oklch(0.6 0.09 235), oklch(0.78 0.09 235))' },
  { token: '--canopy', value: 'light-dark(oklch(0.28 0.05 160), oklch(0.26 0.04 160))' },
  { token: '--focus', value: 'light-dark(oklch(0.55 0.14 90), oklch(0.82 0.14 90))' },
];

const chartPalette = [1, 2, 3, 4, 5, 6, 7, 8].map((step) => `--chart-${step}`);

const spacing = [1, 2, 3, 4, 6, 8, 12, 16];

const motions = [
  { token: '--duration-120', className: 'transition-micro', samples: 'hover · focus · toggles' },
  {
    token: '--duration-240',
    className: 'transition-structural',
    samples: 'drawer · accordion · search',
  },
  { token: '--duration-480', className: 'transition-scene', samples: 'hero · scene entry' },
];

export default async function DesignSystemPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main id="main" className="min-h-dvh pb-24">
      <div className="fixed inset-x-0 top-0 z-50 h-0.5 bg-[var(--line)]">
        <div className="scroll-timeline-indicator h-full w-full bg-[var(--forest)]" />
      </div>

      <header className="contour contour-drift border-b border-[var(--line)]">
        <div className="mx-auto max-w-6xl px-6 py-14">
          <p className="num text-xs text-[var(--ink-soft)]">
            DESIGN_SYSTEM_ART_AND_VISUALS_2026.md
          </p>
          <h1 className="display mt-3 text-balance text-4xl text-[var(--ink)] sm:text-5xl">
            Living Terrain · Design System 2026
          </h1>
          <p className="num mt-4 max-w-2xl text-pretty text-sm text-[var(--ink-soft)]">
            tokens · oklch · logical-properties · light-dark() · motion 120/240/480 · WCAG 2.2 AA
          </p>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <h2 className="num text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §2 COLOR — BIOME PALETTE
        </h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {palette.map((item) => (
            <div key={item.token} className="card flex items-center gap-3 p-3">
              <span
                className="size-10 shrink-0 rounded-[var(--radius-s)] border border-[var(--line)]"
                style={{ background: `var(${item.token})` }}
                aria-hidden="true"
              />
              <span className="min-w-0">
                <span className="num block text-xs font-semibold text-[var(--ink)]">
                  {item.token}
                </span>
                <span className="num block truncate text-[0.65rem] text-[var(--ink-soft)]">
                  {item.value}
                </span>
              </span>
            </div>
          ))}
        </div>

        <h3 className="num mt-10 text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §2.3 CHART PALETTE — COLORBLIND-SAFE
        </h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {chartPalette.map((token) => (
            <div key={token} className="card flex items-center gap-2 px-3 py-2">
              <span
                className="size-4 rounded-full border border-[var(--line)]"
                style={{ background: `var(${token})` }}
                aria-hidden="true"
              />
              <span className="num text-[0.68rem] text-[var(--ink-soft)]">{token}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-12">
        <h2 className="num text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §3 TYPOGRAPHY — MULTI-SCRIPT
        </h2>
        <div className="card mt-5 grid gap-6 p-6">
          <div>
            <span className="num text-[0.65rem] text-[var(--ink-soft)]">--font-display</span>
            <p className="display mt-1 text-3xl text-[var(--ink)]">
              آب · خاک · زندگی — Living Terrain
            </p>
          </div>
          <div>
            <span className="num text-[0.65rem] text-[var(--ink-soft)]">--font-sans</span>
            <p className="mt-1 text-sm text-[var(--ink)]">
              پایداری، امانت‌داری داده و شفافیت علمی برای جوامع محلی و نهادهای جهانی.
            </p>
          </div>
          <div>
            <span className="num text-[0.65rem] text-[var(--ink-soft)]">
              --font-mono · direction:ltr · unicode-bidi:isolate
            </span>
            <p className="num mt-1 text-sm text-[var(--ink)]">
              1,024 · oklch(0.55 0.11 235) · LCP ≤ 2.5s · INP ≤ 200ms · CLS ≤ 0.1
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-12">
        <h2 className="num text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §4.1 SPACING — 4PX GRID
        </h2>
        <div className="card mt-5 flex flex-wrap items-end gap-4 p-6">
          {spacing.map((step) => (
            <div key={step} className="flex flex-col items-center gap-2">
              <span
                className="rounded-[var(--radius-2)] bg-[var(--water)]"
                style={{ width: `${step * 4}px`, height: '12px' }}
                aria-hidden="true"
              />
              <span className="num text-[0.6rem] text-[var(--ink-soft)]">--space-{step}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-12">
        <h2 className="num text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §6 MOTION — 120/240/480 · ease-out-quart
        </h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {motions.map((motion) => (
            <div key={motion.token} className="card group p-5">
              <span className="num block text-xs font-semibold text-[var(--ink)]">
                {motion.token}
              </span>
              <span className="num mt-1 block text-[0.68rem] text-[var(--ink-soft)]">
                {motion.samples}
              </span>
              <div
                className={`mt-4 h-1.5 w-1/3 rounded-full bg-[var(--forest)] group-hover:w-full ${motion.className}`}
                aria-hidden="true"
              />
            </div>
          ))}
        </div>
        <p className="num mt-3 text-[0.68rem] text-[var(--ink-soft)]">
          prefers-reduced-motion → 0.01ms (globals.css motion-budget override)
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-12">
        <h2 className="num text-xs font-semibold tracking-widest text-[var(--ink-soft)]">
          §5 SIGNATURE VISUALS &amp; STATES
        </h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <div className="contour contour-drift card rise relative overflow-hidden p-6">
            <span className="num text-[0.65rem] text-[var(--ink-soft)]">
              .contour · .contour-drift · .rise (CSS-only)
            </span>
            <p className="mt-3 text-sm text-[var(--ink)]">
              کانتور زنده — بدون جاوااسکریپت، با گرادیان‌های تکرارشونده oklch.
            </p>
          </div>

          <div className="card flex flex-col gap-4 p-6">
            <div className="flex flex-wrap items-center gap-3">
              <span className="chip">
                <span className="status-dot" data-state="ok" aria-hidden="true" />
                status-dot[data-state=ok]
              </span>
              <span className="chip">
                <span className="status-dot" data-state="warn" aria-hidden="true" />
                warn
              </span>
              <span className="chip">
                <span className="status-dot" data-state="down" aria-hidden="true" />
                down
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <ProvenanceStamp
                source="station:IRN-YZD-01"
                verified
                method="FAO-56"
                modelConfidence={0.82}
                timestamp="2026-09-22T08:30:00.000Z"
              />
              <ProvenanceStamp source="model-run:latest" verified={false} method="RUSLE" />
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="button" className="btn btn-primary transition-micro">
                btn-primary
              </button>
              <button type="button" className="btn btn-ghost transition-micro">
                btn-ghost
              </button>
            </div>
          </div>
        </div>
      </section>

      <footer className="mx-auto max-w-6xl px-6">
        <div className="card flex flex-wrap items-center justify-between gap-3 p-5">
          <span className="num text-[0.68rem] text-[var(--ink-soft)]">
            §7 green-web · self-hosted fonts · AVIF/WebP · JS ≤ 200KB gzip
          </span>
          <span className="num text-[0.68rem] text-[var(--ink-soft)]">
            WCAG 2.2 AA · axe + keyboard audit in CI
          </span>
        </div>
      </footer>
    </main>
  );
}
