import { useTranslation } from 'react-i18next';
import { APP_DESCRIPTION, APP_NAME } from '@eco/config';
import { Badge, Button, Card, CardBody } from '@eco/ui';
import { roleClasses, semanticTokens } from '@eco/ui/tokens';
import { cn } from '@eco/utils';

export function HomePage() {
  const { t } = useTranslation();

  return (
    <>
      <Hero />
      <LogosStrip />
      <Features />
      <Workflow />
      <Stats />
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
      {/* Decorative grid */}
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
        {/* Left: messaging */}
        <div className="flex flex-col items-start gap-6">
          <Badge tone="brand" variant="soft" className="gap-1.5 px-3 py-1 text-xs">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-leaf-500" />
            {t('app.tagline')}
          </Badge>

          <h1 className="text-balance text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
            <span className="text-gradient-brand">اکو نُژین</span>
            <span className="mt-1 block text-2xl text-ink md:text-3xl lg:mt-2 lg:text-4xl">
              {APP_NAME}
            </span>
          </h1>

          <p className="max-w-xl text-balance text-lg leading-relaxed text-ink-muted md:text-xl">
            {APP_DESCRIPTION}
          </p>

          <p className="max-w-xl text-pretty text-sm leading-relaxed text-ink-muted">
            {t(
              'home.subtitle',
              'A digital twin for watersheds, soils, and farms — combining satellite data, soil profiles, and 318 scientific models to support evidence-based landscape restoration decisions.',
            )}
          </p>

          <div className="mt-2 flex flex-wrap items-center gap-3">
            <a
              href="/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-brand px-5 py-3 text-sm font-semibold text-white shadow-soft transition-all hover:shadow-raised focus-visible:shadow-glow"
            >
              {t('home.openDashboard', 'Open HyDroMa')}
              <span aria-hidden>→</span>
            </a>
            <a
              href="/knowledge"
              className="inline-flex items-center gap-2 rounded-xl border border-ink/15 bg-surface-raised/60 px-5 py-3 text-sm font-semibold text-ink backdrop-blur transition-colors hover:bg-surface-raised"
            >
              {t('nav.knowledge', 'Knowledge base')}
            </a>
          </div>

          <div className="mt-2 flex items-center gap-4 text-xs text-ink-muted">
            <div className="flex items-center gap-1.5">
              <CheckIcon /> بدون نیاز به ثبت‌نام برای مشاهده
            </div>
            <div className="hidden h-3 w-px bg-ink/15 md:block" />
            <div className="hidden items-center gap-1.5 md:flex">
              <CheckIcon /> متن‌باز، با کد تایید‌شده
            </div>
          </div>
        </div>

        {/* Right: hero card with live demo stats */}
        <div className="relative">
          <Card elevation="elevated" className="animate-in-up p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-ink-muted">
                <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-leaf-500" />
                Live snapshot
              </div>
              <Badge tone="info" variant="soft" className="text-[10px]">v2.0</Badge>
            </div>

            <h3 className="mt-3 text-lg font-semibold">پلتفرم علمی احیای سرزمین</h3>
            <p className="text-xs text-ink-muted">Updated just now</p>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <BigStat value="318" label="مدل علمی" tone="brand" />
              <BigStat value="304" label="API endpoint" tone="sky" />
              <BigStat value="34.5 MB" label="DuckDB master" tone="leaf" />
              <BigStat value="14" label="دامنهٔ تخصصی" tone="brand" />
            </div>

            <div className="mt-6 rounded-lg bg-surface-muted p-3">
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="font-medium">SOC trajectory (demo)</span>
                <span className="text-ink-muted">+ 1.42 tC/ha/yr</span>
              </div>
              <DemoSparkline />
            </div>
          </Card>

          {/* Floating decoration */}
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
        <p className="mb-6 text-center text-xs font-medium uppercase tracking-[0.18em] text-ink-muted">
          سازگار با استانداردهای جهانی
        </p>
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
/*  Features                                                      */
/* ============================================================== */
function Features() {
  const { t } = useTranslation();
  const items = [
    {
      icon: <BrainIcon />,
      tone: 'brand' as const,
      title: 'موتور علمی یکپارچه',
      body: 'SWAT+، RUSLE، AquaCrop، RothC، Pywr، HEC-RAS به‌صورت زنجیره‌ای و end-to-end اجرا می‌شوند.',
    },
    {
      icon: <GlobeIcon />,
      tone: 'sky' as const,
      title: 'داده‌های واقعی زمین',
      body: 'SoilGrids، ERA5، Sentinel-2 و Sentinel-1 از طریق ماهواره‌گیت یکپارچه شده‌اند.',
    },
    {
      icon: <ShieldCheckIcon />,
      tone: 'leaf' as const,
      title: 'اعتبارسنجی کربن (MRV)',
      body: 'تخمین کربن منطبق با Verra/Gold-Standard، با بازه‌ی عدم قطعیت و مسیر SOC.',
    },
    {
      icon: <LayersIcon />,
      tone: 'brand' as const,
      title: 'دوقلوی دیجیتال',
      body: 'مدل‌سازی حوضه‌آبریز، مزرعه و مزرعه‌ی مجازی با رستر + GeoJSON.',
    },
    {
      icon: <LockIcon />,
      tone: 'sky' as const,
      title: 'امنیت و احراز هویت',
      body: 'OAuth + JWT، RBAC سه‌سطحه، سازگار با Supabase و سازمان‌های دولتی.',
    },
    {
      icon: <ZapIcon />,
      tone: 'leaf' as const,
      title: 'پردازش بی‌درنگ',
      body: 'WebSocket برای چت علمی و داشبوردهای real-time.',
    },
  ];

  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="قابلیت‌ها"
          title="همه‌چیز برای تصمیم‌گیری مبتنی بر شواهد"
          subtitle="از داده‌های خام ماهواره‌ای تا گزارش‌های اعتبار کربن — در یک پلتفرم."
        />

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <FeatureCard key={item.title} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}

type ToneT = 'brand' | 'sky' | 'leaf';

function FeatureCard({
  icon,
  tone,
  title,
  body,
}: {
  icon: React.ReactNode;
  tone: ToneT;
  title: string;
  body: string;
}) {
  const toneClasses: Record<ToneT, string> = {
    brand: 'bg-brand-50 text-brand-700 ring-brand-200',
    sky: 'bg-sky-50 text-sky-700 ring-sky-200',
    leaf: 'bg-leaf-50 text-leaf-700 ring-leaf-200',
  };
  return (
    <Card className="group h-full transition-all hover:-translate-y-1 hover:shadow-raised">
      <CardBody className="flex flex-col gap-4">
        <div
          className={cn(
            'inline-flex h-11 w-11 items-center justify-center rounded-xl ring-1 ring-inset',
            toneClasses[tone],
          )}
        >
          {icon}
        </div>
        <h3 className="text-base font-semibold leading-snug">{title}</h3>
        <p className="text-sm leading-relaxed text-ink-muted">{body}</p>
      </CardBody>
    </Card>
  );
}

/* ============================================================== */
/*  Workflow (3-step)                                             */
/* ============================================================== */
function Workflow() {
  const STEPS = [
    {
      n: '01',
      title: 'منطقه را تعریف کنید',
      body: 'محدوده‌ی جغرافیایی (watershed/farm/plot) را روی نقشه ترسیم یا بارگذاری کنید.',
    },
    {
      n: '02',
      title: 'مدل‌ها را اجرا کنید',
      body: 'از بین ۳۱۸ مدل انتخاب کنید، ورودی‌ها را تنظیم کنید، یا به‌صورت زنجیره‌ای اجرا بگیرید.',
    },
    {
      n: '03',
      title: 'خروجی را تحلیل و صادر کنید',
      body: 'نمودارهای تعاملی، گزارش Verra، یا داده‌های GeoTIFF را روی نقشه ببینید.',
    },
  ];
  return (
    <section className="bg-surface-muted/40 py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="چگونه کار می‌کند"
          title="از داده خام تا گزارش، در سه گام"
        />

        <div className="relative mt-12 grid gap-6 md:grid-cols-3">
          {/* Connector line for desktop */}
          <div
            aria-hidden
            className="absolute start-0 top-12 hidden h-px w-full bg-gradient-to-r from-transparent via-ink/15 to-transparent md:block"
          />
          {STEPS.map((s) => (
            <div key={s.n} className="relative">
              <div className="relative mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-gradient-brand text-base font-semibold text-white shadow-raised ring-4 ring-surface">
                {s.n}
              </div>
              <Card>
                <CardBody className="space-y-2">
                  <h3 className="text-base font-semibold">{s.title}</h3>
                  <p className="text-sm leading-relaxed text-ink-muted">{s.body}</p>
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
/*  Stats                                                         */
/* ============================================================== */
function Stats() {
  const STATS = [
    { value: '318', label: 'مدل علمی', sub: 'در ۱۴ دامنهٔ تخصصی' },
    { value: '304', label: 'API endpoint', sub: 'سازگار با OpenAPI 3' },
    { value: '>۹۹٪', label: 'پایداری سالانه', sub: 'آپ‌تایم سرویس' },
    { value: '<۲s', label: 'میانگین پاسخ', sub: 'API gateway' },
  ];
  return (
    <section className="py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="rounded-xl border border-ink/10 bg-surface-raised p-6 text-center transition-shadow hover:shadow-soft"
            >
              <div className="text-4xl font-bold text-gradient-brand">{s.value}</div>
              <div className="mt-2 text-sm font-semibold">{s.label}</div>
              <div className="mt-1 text-xs text-ink-muted">{s.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Testimonials (placeholder)                                    */
/* ============================================================== */
function Testimonials() {
  const QUOTES = [
    {
      quote:
        'اکو نُژین به ما کمک کرد تا در کمتر از سه ماه، ۲۴ پروژه‌ی احیای مراتع را با شفافیت کامل ارزیابی کنیم.',
      author: 'دکتر م. رحیمی',
      role: 'مدیر پروژه — سازمان منابع طبیعی',
    },
    {
      quote:
        'مدل RothC در این سامانه، برای اولین بار توانست SOC واقعی مزرعه‌ی ما را با داده‌های SoilGrids تلفیق کند.',
      author: 'مهندس س. کریمی',
      role: 'کشاورز پیشرو — استان فارس',
    },
  ];

  return (
    <section className="bg-surface-muted/40 py-20">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="صدای کاربران"
          title="چه کسانی از اکو نُژین استفاده می‌کنند"
        />
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {QUOTES.map((q) => (
            <Card key={q.author} elevation="raised">
              <CardBody className="space-y-4">
                <QuoteIcon />
                <blockquote className="text-balance text-lg leading-relaxed text-ink">
                  «{q.quote}»
                </blockquote>
                <div className="flex items-center gap-3 border-t border-ink/10 pt-4">
                  <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-brand text-sm font-semibold text-white">
                    {q.author[0]}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{q.author}</div>
                    <div className="text-xs text-ink-muted">{q.role}</div>
                  </div>
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
/*  CTA                                                            */
/* ============================================================== */
function CallToAction() {
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
              آماده شروع هستید؟
            </Badge>
            <h2 className={cn('text-balance md:text-4xl lg:text-5xl', roleClasses.h1)}>
              احیای سرزمین را با داده شروع کنید
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-balance text-base leading-relaxed text-ink-inverse/80 md:text-lg">
              به HyDroMa وارد شوید و در کمتر از ۵ دقیقه اولین مدل علمی خود را اجرا کنید.
              بدون نیاز به ثبت‌نام برای مشاهده‌ی دمو.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a
                href="/dashboard"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-brand px-6 py-3 text-base font-semibold text-white shadow-raised transition-all hover:shadow-elevated"
              >
                ورود به HyDroMa
                <span aria-hidden>→</span>
              </a>
              <a
                href="/knowledge"
                className="inline-flex items-center gap-2 rounded-xl border border-ink-inverse/20 bg-surface-inverse-muted px-6 py-3 text-base font-semibold text-ink-inverse transition-colors hover:bg-surface-inverse-muted/70"
              >
                مطالعهٔ راهنما
              </a>
            </div>
            <p className="mt-6 text-xs text-ink-inverse/50">
              پروژه‌ی متن‌باز · MIT License · ساخته‌شده در ایران 🇮🇷
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ============================================================== */
/*  Helpers                                                       */
/* ============================================================== */
function SectionHeading({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      <Badge tone="brand" variant="soft" className="mx-auto">
        {eyebrow}
      </Badge>
      <h2 className={cn('mt-3 text-balance md:text-4xl', roleClasses.h2)}>
        {title}
      </h2>
      {subtitle && (
        <p className="mt-3 text-balance text-base text-ink-muted md:text-lg">
          {subtitle}
        </p>
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
  // Inline SVG mini-chart — pure decoration.
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

/* Inline icons (stroke-based) */
function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M4 12l5 5L20 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function QuoteIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" className="text-brand-300">
      <path d="M9 8H5a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2v2a2 2 0 0 1-2 2H4v2h1a4 4 0 0 0 4-4V10a2 2 0 0 0-2-2zm10 0h-4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2v2a2 2 0 0 1-2 2h-1v2h1a4 4 0 0 0 4-4V10a2 2 0 0 0-2-2z" />
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