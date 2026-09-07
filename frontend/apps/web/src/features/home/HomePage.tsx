import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge, Card, CardBody } from '@eco/ui';
import { AreaChart, GaugeChart } from '@eco/charts';
import { roleClasses } from '@eco/ui/tokens';
import { cn } from '@eco/utils';

/* ================================================================
   DATA
   ================================================================ */
const MODELS = [
  {
    id: 'swat',
    domain: 'water',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-sky-500 to-cyan-600',
    soft: 'bg-sky-50 dark:bg-sky-950/40',
    ring: 'ring-sky-200 dark:ring-sky-800',
    text: 'text-sky-700 dark:text-sky-300',
    badge: 'bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-200',
  },
  {
    id: 'pywr',
    domain: 'water',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" /><circle cx="12" cy="18" r="3" />
        <path d="M8.5 7.5L10.5 16.5M15.5 7.5L13.5 16.5M6 9h12" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-teal-500 to-emerald-600',
    soft: 'bg-teal-50 dark:bg-teal-950/40',
    ring: 'ring-teal-200 dark:ring-teal-800',
    text: 'text-teal-700 dark:text-teal-300',
    badge: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-200',
  },
  {
    id: 'hecras',
    domain: 'hydraulic',
    domainKey: 'models.domains.hydraulic',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 12h4l3-9 4 18 3-9h4" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
    gradient: 'from-indigo-500 to-blue-700',
    soft: 'bg-indigo-50 dark:bg-indigo-950/40',
    ring: 'ring-indigo-200 dark:ring-indigo-800',
    text: 'text-indigo-700 dark:text-indigo-300',
    badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200',
  },
  {
    id: 'aquacrop',
    domain: 'crop',
    domainKey: 'models.domains.crop',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 22V12" strokeLinecap="round" />
        <path d="M12 12c-2-4-6-5-6-5s3 2 6-2c3 4 6 2 6 2s-4-1-6-5z" strokeLinejoin="round" />
        <path d="M12 16c1.5-3 4.5-4 4.5-4s-2 1-4.5-2z" strokeLinejoin="round" opacity="0.5" />
      </svg>
    ),
    gradient: 'from-lime-500 to-green-700',
    soft: 'bg-lime-50 dark:bg-lime-950/40',
    ring: 'ring-lime-200 dark:ring-lime-800',
    text: 'text-lime-700 dark:text-lime-300',
    badge: 'bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-200',
  },
  {
    id: 'rusle',
    domain: 'erosion',
    domainKey: 'models.domains.erosion',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 20h18" strokeLinecap="round" />
        <path d="M6 20l4-10 4 6 4-8 4 12" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
    gradient: 'from-amber-500 to-orange-700',
    soft: 'bg-amber-50 dark:bg-amber-950/40',
    ring: 'ring-amber-200 dark:ring-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200',
  },
  {
    id: 'rothc',
    domain: 'carbon',
    domainKey: 'models.domains.carbon',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-emerald-500 to-teal-700',
    soft: 'bg-emerald-50 dark:bg-emerald-950/40',
    ring: 'ring-emerald-200 dark:ring-emerald-800',
    text: 'text-emerald-700 dark:text-emerald-300',
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200',
  },
];

const STATS = [
  { value: '318+', labelKey: 'nav.models', fallback: 'Scientific Models', tone: 'brand' as const },
  { value: '14', labelKey: 'home.domains', fallback: 'Domains', tone: 'sky' as const },
  { value: '190+', labelKey: 'home.countries', fallback: 'Countries', tone: 'leaf' as const },
  { value: '99.9%', labelKey: 'home.uptime', fallback: 'Uptime', tone: 'brand' as const },
];

const TRUST = [
  'Sentinel-2', 'ESA', 'NASA', 'ECMWF ERA5', 'SoilGrids', 'FAO AquaCrop',
  'USDA', 'Verra VCS', 'Gold Standard', 'IPCC AR6', 'OpenET', 'CGIAR',
];

/* ================================================================
   HOME PAGE
   ================================================================ */
export function HomePage() {
  return (
    <>
      <Hero />
      <ModelsShowcase />
      <GlobalStats />
      <TrustMarquee />
      <CallToAction />
    </>
  );
}

/* ================================================================
   HERO
   ================================================================ */
function Hero() {
  const { t } = useTranslation();
  return (
    <section className="relative isolate overflow-hidden">
      {/* ── Background layers ── */}
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
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        {[...Array(12)].map((_, i) => (
          <span
            key={i}
            className="absolute inline-block h-1.5 w-1.5 rounded-full bg-ink/10 dark:bg-white/10"
            style={{
              top: `${15 + Math.random() * 70}%`,
              left: `${5 + Math.random() * 90}%`,
              animation: `float ${4 + Math.random() * 6}s ease-in-out infinite`,
              animationDelay: `${Math.random() * 5}s`,
            }}
          />
        ))}
      </div>

      {/* ── Content ── */}
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
                href="/dashboard"
                className="inline-flex h-12 items-center gap-2 rounded-full bg-ink px-7 text-sm font-semibold text-ink-inverse shadow-raised transition-all hover:-translate-y-0.5 hover:shadow-elevated focus-visible:shadow-glow focus-visible:outline-none"
              >
                {t('home.openDashboard')}
                <span aria-hidden className="rtl-flip">→</span>
              </a>
              <a
                href="/models"
                className="inline-flex h-12 items-center gap-2 rounded-full border border-ink/15 bg-surface-raised/70 px-7 text-sm font-semibold text-ink backdrop-blur transition-colors hover:bg-surface-raised"
              >
                {t('nav.models')}
              </a>
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

        {/* ── Live snapshot preview ── */}
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
                <AnimatedStat value={26} suffix="%" label={t('finance.irr')} tone="brand" />
                <AnimatedStat value={2.8} suffix="×" label={t('finance.bc')} tone="sky" />
                <AnimatedStat value={318} suffix="" label={t('nav.models')} tone="leaf" />
                <AnimatedStat value={4.2} suffix=" yr" label={t('finance.payback')} tone="brand" />
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-ink/10 bg-surface-muted/60 p-4">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-medium">SOC trajectory (demo)</span>
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
                    <span className="text-brand-700 dark:text-brand-300">26%</span>
                  </div>
                  <GaugeChart value={26} min={0} max={100} unit="%" height={140} />
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

/* ================================================================
   MODELS SHOWCASE — COLORFUL 3D CARDS
   ================================================================ */
function ModelsShowcase() {
  const { t } = useTranslation();
  return (
    <section className="relative overflow-hidden py-24 lg:py-32">
      {/* Background texture */}
      <div aria-hidden className="absolute inset-0 -z-10 bg-surface-muted/40" />
      <div aria-hidden className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_50%,rgba(175,95,30,0.06),transparent_45%),radial-gradient(circle_at_80%_50%,rgba(6,182,212,0.06),transparent_45%)]" />

      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="brand" variant="soft" className="mx-auto">{t('models.title')}</Badge>
            <h2 className={cn('mt-4 text-balance text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl', roleClasses.h2)}>
              {t('models.title')}
            </h2>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">{t('models.subtitle')}</p>
          </div>
        </Reveal>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MODELS.map((m, i) => (
            <Reveal key={m.id} delay={i * 80}>
              <a
                href="/dashboard"
                className="group block h-full"
              >
                <div
                  className={cn(
                    'card-3d relative h-full overflow-hidden rounded-2xl border border-ink/10 bg-surface-raised p-6 transition-all duration-500 hover:shadow-elevated',
                    m.soft,
                  )}
                >
                  {/* Gradient header bar */}
                  <div className={cn('absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r', m.gradient)} />

                  <div className="flex items-center justify-between">
                    <div className={cn('grid h-12 w-12 place-items-center rounded-xl', m.badge)}>
                      {m.icon}
                    </div>
                    <span className={cn('rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider', m.badge)}>
                      {t(m.domainKey, m.domain)}
                    </span>
                  </div>

                  <h3 className="mt-4 text-lg font-semibold text-ink">
                    {t(`models.${m.id}.name`, m.id.toUpperCase())}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                    {t(`models.${m.id}.desc`)}
                  </p>

                  <div className="mt-5 flex items-center gap-2 text-sm font-semibold text-ink-muted transition-colors group-hover:text-ink">
                    <span>{t('models.launch', 'Launch in HyDroMa')}</span>
                    <span aria-hidden className="rtl-flip">→</span>
                  </div>
                </div>
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ================================================================
   GLOBAL STATS
   ================================================================ */
function GlobalStats() {
  const { t } = useTranslation();
  return (
    <section className="border-y border-ink/10 bg-surface-inverse py-16 text-ink-inverse dark:border-ink/10">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          {STATS.map((s, i) => (
            <Reveal key={s.value} delay={i * 60}>
              <div className="text-center">
                <div className="text-4xl font-bold tracking-tight text-brand-300 dark:text-brand-200">{s.value}</div>
                <div className="mt-2 text-xs uppercase tracking-wider text-ink-inverse/60">
                  {t(s.labelKey, s.fallback)}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ================================================================
   TRUST MARQUEE
   ================================================================ */
function TrustMarquee() {
  const { t } = useTranslation();
  const loop = [...TRUST, ...TRUST];
  return (
    <section className="overflow-hidden border-b border-ink/10 bg-surface py-10">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-ink-muted">
          {t('home.trustLabel')}
        </p>
      </div>
      <div className="relative mt-6">
        <div className="pointer-events-none absolute inset-y-0 start-0 z-10 w-24 bg-gradient-to-r from-surface to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 end-0 z-10 w-24 bg-gradient-to-l from-surface to-transparent" />
        <div className="marquee gap-12">
          {loop.map((label, i) => (
            <span key={`${label}-${i}`} className="whitespace-nowrap text-lg font-semibold tracking-tight text-ink-muted/70">
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ================================================================
   CALL TO ACTION
   ================================================================ */
function CallToAction() {
  const { t } = useTranslation();
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl bg-ink px-8 py-16 text-center text-ink-inverse shadow-elevated sm:px-12 lg:py-20">
            <div
              aria-hidden
              className="absolute inset-0 opacity-25"
              style={{
                backgroundImage:
                  'radial-gradient(circle at 15% 20%, rgb(var(--color-brand-400)) 0%, transparent 40%), radial-gradient(circle at 80% 80%, rgb(var(--color-sky-400)) 0%, transparent 45%)',
              }}
            />
            <div className="relative">
              <Badge tone="brand" variant="solid" className="mx-auto mb-6">{t('cta.badge')}</Badge>
              <h2 className="mx-auto max-w-2xl text-balance text-4xl font-bold tracking-tight sm:text-5xl">{t('cta.title')}</h2>
              <p className="mx-auto mt-5 max-w-2xl text-balance text-base leading-relaxed text-ink-inverse/80 md:text-lg">{t('cta.body')}</p>
              <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                <a
                  href="/dashboard"
                  className="inline-flex h-12 items-center gap-2 rounded-full bg-white px-7 text-sm font-semibold text-ink shadow-raised transition-all hover:-translate-y-0.5 hover:shadow-elevated"
                >
                  {t('home.openDashboard')}
                  <span aria-hidden className="rtl-flip">→</span>
                </a>
                <a
                  href="/knowledge"
                  className="inline-flex h-12 items-center gap-2 rounded-full border border-ink-inverse/20 bg-ink-inverse/5 px-7 text-sm font-semibold text-ink-inverse transition-colors hover:bg-ink-inverse/10"
                >
                  {t('cta.secondary')}
                </a>
              </div>
              <p className="mt-8 text-xs text-ink-inverse/50">{t('cta.footer')}</p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ================================================================
   HELPERS
   ================================================================ */
function Reveal({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setInView(true);
            io.disconnect();
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -48px 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={cn('reveal', inView && 'in', className)}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

function AnimatedStat({ value, suffix = '', label, tone }: { value: number; suffix?: string; label: string; tone: 'brand' | 'sky' | 'leaf' }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const duration = 1800;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * ease);
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [value]);
  const colors: Record<string, string> = {
    brand: 'text-brand-700 dark:text-brand-300',
    sky: 'text-sky-700 dark:text-sky-300',
    leaf: 'text-leaf-700 dark:text-leaf-300',
  };
  const formatted = Number.isInteger(value) ? Math.round(display).toLocaleString() : display.toFixed(1);
  return (
    <div className="rounded-xl border border-ink/10 bg-surface-muted p-4">
      <div className={cn('text-2xl font-bold tracking-tight', colors[tone])}>
        {formatted}{suffix}
      </div>
      <div className="mt-1 text-xs text-ink-muted">{label}</div>
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
