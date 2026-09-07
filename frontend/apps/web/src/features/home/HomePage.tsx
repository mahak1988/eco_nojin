import { useTranslation } from 'react-i18next';
import { APP_NAME } from '@eco/config';
import { Badge, Button, Card, CardBody } from '@eco/ui';
import { roleClasses } from '@eco/ui/tokens';
import { cn } from '@eco/utils';

export function HomePage() {
  return (
    <>
      <Hero />
      <LogosStrip />
      <Crises />
      <Principles />
      <Features />
      <Workflow />
      <FinanceStrip />
      <ImpactGrid />
      <Testimonials />
      <CallToAction />
    </>
  );
}

/* ============================================================== */
/*  Hero                                                          */
/* ============================================================== */
function Hero() {
  const { t } = useTranslation();
  return (
    <section className="bg-mesh relative isolate overflow-hidden surface-hero">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[0.35]"
        style={{
          backgroundImage:
            'radial-gradient(circle at 25% 30%, rgb(var(--color-brand-200)) 0%, transparent 50%), radial-gradient(circle at 80% 70%, rgb(var(--color-sky-200)) 0%, transparent 55%)',
        }}
      />
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 -z-10 h-px bg-gradient-to-r from-transparent via-brand-400/30 to-transparent"
      />

      <div className="mx-auto grid w-full max-w-content gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:gap-16 lg:py-28 lg:px-8">
        <div className="flex flex-col items-start gap-6">
          <Badge tone="brand" variant="soft" className="gap-1.5 px-3 py-1 text-xs">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-leaf-500" />
            {t('app.tagline')}
          </Badge>

          <h1 className="text-balance text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
            <span className="text-gradient-brand">{t('home.heroTitle')}</span>
            <span className="mt-1 block text-2xl text-ink md:text-3xl lg:mt-2 lg:text-4xl">
              {APP_NAME}
            </span>
          </h1>

          <p className="max-w-xl text-balance text-lg leading-relaxed text-ink-muted md:text-xl">
            {t('home.heroSubtitle')}
          </p>

          <p className="max-w-xl text-pretty text-sm leading-relaxed text-ink-muted">
            {t('home.subtitle')}
          </p>

          <div className="mt-2 flex flex-wrap items-center gap-3">
            <a
              href="/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-brand px-5 py-3 text-sm font-semibold text-white shadow-soft transition-all hover:shadow-raised focus-visible:shadow-glow"
            >
              {t('home.openDashboard')}
              <span aria-hidden>→</span>
            </a>
            <a
              href="/knowledge"
              className="inline-flex items-center gap-2 rounded-xl border border-ink/15 bg-surface-raised/60 px-5 py-3 text-sm font-semibold text-ink backdrop-blur transition-colors hover:bg-surface-raised"
            >
              {t('nav.knowledge')}
            </a>
          </div>

          <div className="mt-2 flex items-center gap-4 text-xs text-ink-muted">
            <div className="flex items-center gap-1.5">
              <CheckIcon /> {t('home.noSignup')}
            </div>
            <div className="hidden h-3 w-px bg-ink/15 md:block" />
            <div className="hidden items-center gap-1.5 md:flex">
              <CheckIcon /> {t('home.openSource')}
            </div>
          </div>
        </div>

        <div className="relative">
          <Card elevation="elevated" className="animate-in-up p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-ink-muted">
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-leaf-500" />
                {t('home.liveSnapshot')}
              </div>
              <Badge tone="info" variant="soft" className="text-[10px]">v2.0</Badge>
            </div>

            <h3 className="mt-3 text-lg font-semibold">{t('home.platformTitle')}</h3>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <BigStat value={t('finance.irrValue')} label={t('finance.irr')} tone="brand" />
              <BigStat value={t('finance.bcValue')} label={t('finance.bc')} tone="sky" />
              <BigStat value="318" label={t('workflow.s2.body', '').slice(0, 12) || 'Models'} tone="leaf" />
              <BigStat value={t('finance.paybackValue')} label={t('finance.payback')} tone="brand" />
            </div>

            <div className="mt-6 rounded-lg bg-surface-muted p-3">
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="font-medium">SOC trajectory (demo)</span>
                <span className="text-ink-muted">+ 1.42 tC/ha/yr</span>
              </div>
              <DemoSparkline />
            </div>
          </Card>

          <div
            aria-hidden
            className="absolute -bottom-6 -end-6 -z-10 h-32 w-32 rounded-full bg-gradient-brand opacity-20 blur-2xl"
          />
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Trust strip                                                   */
/* ============================================================== */
function LogosStrip() {
  const ITEMS = ['Sentinel-2', 'ERA5', 'SoilGrids', 'Verra VCS', 'Gold Standard', 'IPCC AR6'];
  return (
    <section className="border-y border-ink/10 bg-surface-muted/50 py-8">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
          {ITEMS.map((label) => (
            <span
              key={label}
              className="text-base font-semibold tracking-tight text-ink-muted/80 transition-colors hover:text-ink"
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Four Crises (NEW — from the strategic document)               */
/* ============================================================== */
function Crises() {
  const { t } = useTranslation();
  const items = [
    { key: 'water', tone: 'sky' as const, icon: <DropIcon /> },
    { key: 'soil', tone: 'leaf' as const, icon: <LayersIcon /> },
    { key: 'livelihood', tone: 'brand' as const, icon: <PeopleIcon /> },
    { key: 'climate', tone: 'sky' as const, icon: <ThermIcon /> },
  ];
  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow={t('crises.title')}
          title={t('crises.subtitle')}
        />
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((it) => (
            <Card key={it.key} className="group h-full transition-all hover:-translate-y-1 hover:shadow-raised">
              <CardBody className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-ink-muted">{t(`crises.${it.key}.title`)}</span>
                  {it.icon}
                </div>
                <div className="text-3xl font-bold text-gradient-brand">{t(`crises.${it.key}.stat`)}</div>
                <p className="text-sm leading-relaxed text-ink-muted">{t(`crises.${it.key}.body`)}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Four Principles (NEW)                                          */
/* ============================================================== */
function Principles() {
  const { t } = useTranslation();
  const keys = ['p1', 'p2', 'p3', 'p4'];
  return (
    <section className="bg-surface-muted/40 py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow={t('principles.title')}
          title={t('principles.subtitle')}
        />
        <div className="mt-12 grid gap-5 md:grid-cols-2">
          {keys.map((k, i) => (
            <Card key={k}>
              <CardBody className="flex gap-4">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-brand text-sm font-semibold text-white shadow-soft">
                  {String(i + 1).padStart(2, '0')}
                </div>
                <div>
                  <h3 className="text-base font-semibold leading-snug">{t(`principles.${k}.title`)}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-ink-muted">{t(`principles.${k}.body`)}</p>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Features (i18n-ized)                                           */
/* ============================================================== */
function Features() {
  const { t } = useTranslation();
  const items = [
    { icon: <BrainIcon />, tone: 'brand' as const, k: 'f1' },
    { icon: <GlobeIcon />, tone: 'sky' as const, k: 'f2' },
    { icon: <ShieldCheckIcon />, tone: 'leaf' as const, k: 'f3' },
    { icon: <LayersIcon />, tone: 'brand' as const, k: 'f4' },
    { icon: <LockIcon />, tone: 'sky' as const, k: 'f5' },
    { icon: <ZapIcon />, tone: 'leaf' as const, k: 'f6' },
  ];
  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow={t('features.eyebrow')}
          title={t('features.title')}
        />
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <FeatureCard
              key={item.k}
              icon={item.icon}
              tone={item.tone}
              title={t(`features.${item.k}.title`)}
              body={t(`features.${item.k}.body`)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

type ToneT = 'brand' | 'sky' | 'leaf';

function FeatureCard({ icon, tone, title, body }: { icon: React.ReactNode; tone: ToneT; title: string; body: string }) {
  const toneClasses: Record<ToneT, string> = {
    brand: 'bg-brand-50 text-brand-700 ring-brand-200',
    sky: 'bg-sky-50 text-sky-700 ring-sky-200',
    leaf: 'bg-leaf-50 text-leaf-700 ring-leaf-200',
  };
  return (
    <Card className="group h-full transition-all hover:-translate-y-1 hover:shadow-raised">
      <CardBody className="flex flex-col gap-4">
        <div className={cn('inline-flex h-11 w-11 items-center justify-center rounded-xl ring-1 ring-inset', toneClasses[tone])}>
          {icon}
        </div>
        <h3 className="text-base font-semibold leading-snug">{title}</h3>
        <p className="text-sm leading-relaxed text-ink-muted">{body}</p>
      </CardBody>
    </Card>
  );
}

/* ============================================================== */
/*  Workflow (i18n-ized)                                           */
/* ============================================================== */
function Workflow() {
  const { t } = useTranslation();
  const steps = ['s1', 's2', 's3'];
  return (
    <section className="bg-surface-muted/40 py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow={t('workflow.eyebrow')} title={t('workflow.title')} />
        <div className="relative mt-12 grid gap-6 md:grid-cols-3">
          <div aria-hidden className="absolute start-0 top-12 hidden h-px w-full bg-gradient-to-r from-transparent via-ink/15 to-transparent md:block" />
          {steps.map((s, i) => (
            <div key={s} className="relative">
              <div className="relative mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-gradient-brand text-base font-semibold text-white shadow-raised ring-4 ring-surface">
                {String(i + 1).padStart(2, '0')}
              </div>
              <Card>
                <CardBody className="space-y-2">
                  <h3 className="text-base font-semibold">{t(`workflow.${s}.title`)}</h3>
                  <p className="text-sm leading-relaxed text-ink-muted">{t(`workflow.${s}.body`)}</p>
                </CardBody>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Finance (NEW — global figures, no pilot names)                 */
/* ============================================================== */
function FinanceStrip() {
  const { t } = useTranslation();
  const cells = [
    { label: t('finance.irr'), value: t('finance.irrValue') },
    { label: t('finance.npv'), value: t('finance.npvValue') },
    { label: t('finance.bc'), value: t('finance.bcValue') },
    { label: t('finance.payback'), value: t('finance.paybackValue') },
  ];
  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow={t('finance.title')} title={t('finance.subtitle')} />
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {cells.map((c) => (
            <div key={c.label} className="rounded-xl border border-ink/10 bg-surface-raised p-6 text-center transition-shadow hover:shadow-soft">
              <div className="text-3xl font-bold text-gradient-brand">{c.value}</div>
              <div className="mt-2 text-sm font-semibold">{c.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Impact (NEW)                                                   */
/* ============================================================== */
function ImpactGrid() {
  const { t } = useTranslation();
  const cells = [
    { k: 'wue', icon: <DropIcon /> },
    { k: 'soc', icon: <LayersIcon /> },
    { k: 'erosion', icon: <ShieldCheckIcon /> },
    { k: 'income', icon: <PeopleIcon /> },
    { k: 'jobs', icon: <ZapIcon /> },
    { k: 'villages', icon: <GlobeIcon /> },
  ];
  return (
    <section className="bg-surface-muted/40 py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading title={t('impact.title')} />
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cells.map((c) => (
            <div key={c.k} className="flex items-center gap-3 rounded-xl border border-ink/10 bg-surface-raised p-4">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-leaf-50 text-leaf-700 ring-1 ring-inset ring-leaf-200">
                {c.icon}
              </span>
              <span className="text-sm font-medium leading-snug">{t(`impact.${c.k}`)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Testimonials — placeholder, to be replaced with real ones      */
/* ============================================================== */
function Testimonials() {
  return null; // TODO: real multilingual testimonials in a later pass
}

/* ============================================================== */
/*  CTA (i18n-ized)                                                */
/* ============================================================== */
function CallToAction() {
  const { t } = useTranslation();
  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-surface-inverse px-8 py-16 text-center text-ink-inverse shadow-elevated sm:px-12">
          <div
            aria-hidden
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage:
                'radial-gradient(circle at 15% 20%, rgb(var(--color-brand-400)) 0%, transparent 40%), radial-gradient(circle at 80% 80%, rgb(var(--color-sky-400)) 0%, transparent 45%)',
            }}
          />
          <div className="relative">
            <Badge tone="brand" variant="solid" className="mx-auto mb-4">
              {t('cta.badge')}
            </Badge>
            <h2 className={cn('text-balance md:text-4xl lg:text-5xl', roleClasses.h1)}>
              {t('cta.title')}
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-balance text-base leading-relaxed text-ink-inverse/80 md:text-lg">
              {t('cta.body')}
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a
                href="/dashboard"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-brand px-6 py-3 text-base font-semibold text-white shadow-raised transition-all hover:shadow-elevated"
              >
                {t('home.openDashboard')}
                <span aria-hidden>→</span>
              </a>
              <a
                href="/knowledge"
                className="inline-flex items-center gap-2 rounded-xl border border-ink-inverse/20 bg-surface-inverse-muted px-6 py-3 text-base font-semibold text-ink-inverse transition-colors hover:bg-surface-inverse-muted/70"
              >
                {t('cta.secondary')}
              </a>
            </div>
            <p className="mt-6 text-xs text-ink-inverse/50">{t('cta.footer')}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Helpers (unchanged)                                            */
/* ============================================================== */
function SectionHeading({ eyebrow, title, subtitle }: { eyebrow?: string; title: string; subtitle?: string }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      {eyebrow && (
        <Badge tone="brand" variant="soft" className="mx-auto">
          {eyebrow}
        </Badge>
      )}
      <h2 className={cn('mt-3 text-balance md:text-4xl', roleClasses.h2)}>{title}</h2>
      {subtitle && (
        <p className="mt-3 text-balance text-base text-ink-muted md:text-lg">{subtitle}</p>
      )}
    </div>
  );
}

function BigStat({ value, label, tone }: { value: string; label: string; tone: ToneT }) {
  const colors: Record<ToneT, string> = {
    brand: 'text-brand-700',
    sky: 'text-sky-700',
    leaf: 'text-leaf-700',
  };
  return (
    <div className="rounded-lg border border-ink/10 bg-surface-muted p-4">
      <div className={cn('text-2xl font-bold', colors[tone])}>{value}</div>
      <div className="mt-1 text-xs text-ink-muted">{label}</div>
    </div>
  );
}

function DemoSparkline() {
  const points = [10, 12, 11, 14, 13, 16, 18, 17, 20, 22, 24, 26];
  const max = Math.max(...points);
  const min = Math.min(...points);
  const w = 240;
  const h = 40;
  const path = points
    .map((v, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - ((v - min) / (max - min)) * h;
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-10 w-full overflow-visible">
      <defs>
        <linearGradient id="spark-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgb(var(--color-leaf-500))" stopOpacity="0.4" />
          <stop offset="100%" stopColor="rgb(var(--color-leaf-500))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L ${w} ${h} L 0 ${h} Z`} fill="url(#spark-area)" />
      <path d={path} stroke="rgb(var(--color-leaf-600))" strokeWidth="2" fill="none" />
    </svg>
  );
}

/* Icons */
function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M4 12l5 5L20 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function DropIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" strokeLinejoin="round" />
    </svg>
  );
}
function PeopleIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3.5 19a5.5 5.5 0 0 1 11 0" strokeLinecap="round" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M15 19a4.5 4.5 0 0 1 6-4.2" strokeLinecap="round" />
    </svg>
  );
}
function ThermIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4 4 0 1 0 4 0z" strokeLinejoin="round" />
    </svg>
  );
}
function BrainIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 4a3 3 0 0 0-3 3v.5A3 3 0 0 0 4 11v.5A3 3 0 0 0 7 14v1a3 3 0 0 0 4 3M15 4a3 3 0 0 1 3 3v.5a3 3 0 0 1 2 3.5v.5a3 3 0 0 1-3 2.5v1a3 3 0 0 1-4 3M9 18h6" strokeLinecap="round" />
    </svg>
  );
}
function GlobeIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}
function ShieldCheckIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function LayersIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3l10 5-10 5L2 8l10-5zM2 12l10 5 10-5M2 17l10 5 10-5" strokeLinejoin="round" />
    </svg>
  );
}
function LockIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}
function ZapIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M13 2L4 14h7l-2 8 9-12h-7l2-8z" strokeLinejoin="round" />
    </svg>
  );
}