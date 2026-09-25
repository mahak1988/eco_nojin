'use client';

import { type CSSProperties, type ReactNode, useState } from 'react';

type Theme = 'light' | 'dark';
type LayerId = 'water' | 'soil' | 'biodiversity';
type ScenarioId = 'balanced' | 'accelerated';

type IconName =
  | 'arrow'
  | 'check'
  | 'database'
  | 'globe'
  | 'home'
  | 'leaf'
  | 'map'
  | 'moon'
  | 'report'
  | 'spark'
  | 'sun'
  | 'water';

const copy = {
  fa: {
    localeName: 'فارسی',
    prototype: 'پروتوتایپ زنده',
    eyebrow: 'هوش زمین برای تصمیم‌های روزمره',
    title: 'از داده‌های زنده تا تصمیم پایدار',
    description:
      'مشاهدهٔ آب، خاک، اقلیم و تنوع زیستی در یک فضای یکپارچه، با منشأ روشن، عدم‌قطعیت قابل فهم و عملکرد آفلاین.',
    primaryCta: 'مشاهدهٔ زنده',
    secondaryCta: 'سناریوی آینده',
    coverage: 'پوشش داده',
    stations: 'ایستگاه فعال',
    lastSync: 'نمونهٔ همگام‌سازی',
    minutes: 'دقیقهٔ نمونه',
    navigation: ['خانه', 'نقشه', 'علم', 'گزارش'],
    overview: 'نمای کلی زنده',
    location: 'حوضهٔ نمونهٔ مرکزی',
    synced: 'نمونه',
    pulse: 'نبض منطقه',
    pulseDescription: 'نمای نمونهٔ لایه‌های مشاهده، مدل و سناریو در یک نما',
    water: 'آب',
    soil: 'خاک',
    biodiversity: 'تنوع زیستی',
    layer: 'لایهٔ فعال',
    modelNote: 'خروجی مدل با عدم‌قطعیت ۱۲٪',
    waterValue: '۶۸٪ ظرفیت',
    soilValue: '۷۴٪ سلامت',
    biodiversityValue: '۸۱٪ پایداری',
    waterDetail: 'رطوبت و منابع آب',
    soilDetail: 'مواد آلی و ساختار',
    biodiversityDetail: 'پوشش و شکل زیستی',
    keySignals: 'سیگنال‌های کلیدی',
    waterMetric: 'آب قابل دسترس',
    soilMetric: 'سلامت خاک',
    climateMetric: 'ریسک اقلیم',
    natureMetric: 'تنوع زیستی',
    stable: 'پایدار',
    watch: 'نیازمند پایش',
    impactPath: 'مسیر اثر',
    impactPathDescription: 'هر داده باید به فهم، اقدام و سنجش برسد.',
    observe: 'مشاهده',
    interpret: 'تفسیر',
    act: 'اقدام',
    evaluate: 'سنجش',
    observeDetail: 'داده معتبر و زمینه‌مند',
    interpretDetail: 'مقایسه با آستانه و تاریخ',
    actDetail: 'پیشنهاد قابل تأیید',
    evaluateDetail: 'بازخورد و اثر واقعی',
    impactLens: 'عدسی اثر پایدار',
    impactDescription: 'نگاشت مفهومی، نه رتبه‌بندی یا امتیاز رسمی.',
    domainLabel: 'زمین · آب · اقلیم · تنوع زیستی',
    impactPrefix: 'اثر',
    global: 'جهانی',
    localProxy: 'شاخص محلی',
    selectedGoal: 'هدف انتخاب‌شده',
    sampleData: 'دادهٔ نمونه',
    illustrative: 'نمایشی',
    scenario: 'سناریوی پیشنهادی',
    scenarioDescription: 'اثر مدیریت آبیاری در افق ۱۴۰۵',
    balanced: 'متعادل',
    accelerated: 'شتاب‌دار',
    scenarioResult: 'مصرف آب',
    scenarioYield: 'عملکرد محصول',
    scenarioRisk: 'ریسک اقلیم',
    scenarioModel: 'مدل پیشنهادی، نه پیش‌بینی قطعی',
    evidence: 'شواهد و کیفیت داده',
    evidenceDescription:
      'هر عدد در این Prototype نمونه است و مسیر داده را برای بازبینی نشان می‌دهد.',
    source: 'منبع',
    method: 'روش',
    coverageLabel: 'پوشش',
    freshness: 'تازگی',
    sourceValue: 'قرارداد دادهٔ نمونه',
    methodValue: 'مدل تعاملی پروتوتایپ',
    coverageValue: '۱۲ منطقهٔ نمونه',
    freshnessValue: 'شبیه‌سازی‌شده',
    actionQueue: 'اقدام‌های نمونه',
    actionOne: 'بازبینی برنامهٔ آبیاری منطقهٔ شرق',
    actionOneMeta: 'اثر بالا · عدم‌قطعیت کم',
    actionTwo: 'ثبت مشاهدهٔ پوشش گیاهی',
    actionTwoMeta: 'مشارکت میدانی · ۸ دقیقه',
    offlineQueue: 'نمونه: ۲ مشاهده در صف ارسال',
    footerNote: 'داده‌های نمونه، سناریوی فرضی و پیشنهاد مدیریتی هرگز یکی نیستند.',
  },
  en: {
    localeName: 'English',
    prototype: 'Living prototype',
    eyebrow: 'Earth intelligence for everyday decisions',
    title: 'From living data to sustainable action',
    description:
      'See water, soil, climate, and biodiversity in one evidence-led workspace with clear provenance, understandable uncertainty, and offline resilience.',
    primaryCta: 'View live pulse',
    secondaryCta: 'Explore a scenario',
    coverage: 'Data coverage',
    stations: 'Active stations',
    lastSync: 'Sample sync',
    minutes: 'sample minutes ago',
    navigation: ['Home', 'Map', 'Science', 'Reports'],
    overview: 'Living overview',
    location: 'Central basin pilot',
    synced: 'Demo',
    pulse: 'Regional pulse',
    pulseDescription: 'Sample observation, model, and scenario layers in one view',
    water: 'Water',
    soil: 'Soil',
    biodiversity: 'Biodiversity',
    layer: 'Active layer',
    modelNote: 'Model output with 12% uncertainty',
    waterValue: '68% capacity',
    soilValue: '74% health',
    biodiversityValue: '81% resilience',
    waterDetail: 'Moisture and water availability',
    soilDetail: 'Organic matter and structure',
    biodiversityDetail: 'Cover and ecological form',
    keySignals: 'Key signals',
    waterMetric: 'Water availability',
    soilMetric: 'Soil health',
    climateMetric: 'Climate risk',
    natureMetric: 'Biodiversity',
    stable: 'Stable',
    watch: 'Monitor',
    impactPath: 'Impact pathway',
    impactPathDescription: 'Every signal should lead to understanding, action, and evaluation.',
    observe: 'Observe',
    interpret: 'Interpret',
    act: 'Act',
    evaluate: 'Evaluate',
    observeDetail: 'Valid, contextual evidence',
    interpretDetail: 'Thresholds and time comparison',
    actDetail: 'Human-approved recommendation',
    evaluateDetail: 'Feedback and real-world impact',
    impactLens: 'Impact lens',
    impactDescription: 'A conceptual map, not a ranking or official score.',
    domainLabel: 'LAND · WATER · CLIMATE · BIODIVERSITY',
    impactPrefix: 'Impact',
    global: 'Global framework',
    localProxy: 'Local proxy',
    selectedGoal: 'Selected goal',
    sampleData: 'Sample data',
    illustrative: 'Illustrative',
    scenario: 'Suggested scenario',
    scenarioDescription: 'Irrigation strategy impact through 2046',
    balanced: 'Balanced',
    accelerated: 'Accelerated',
    scenarioResult: 'Water use',
    scenarioYield: 'Crop yield',
    scenarioRisk: 'Climate risk',
    scenarioModel: 'Suggested model, not a certainty',
    evidence: 'Evidence and data quality',
    evidenceDescription:
      'Every number in this prototype is illustrative and exposes the evidence path for review.',
    source: 'Source',
    method: 'Method',
    coverageLabel: 'Coverage',
    freshness: 'Freshness',
    sourceValue: 'Illustrative data contract',
    methodValue: 'Prototype interaction model',
    coverageValue: '12 sample regions',
    freshnessValue: 'Simulated',
    actionQueue: 'Sample next actions',
    actionOne: 'Review irrigation plan for eastern district',
    actionOneMeta: 'High impact · Low uncertainty',
    actionTwo: 'Submit a vegetation observation',
    actionTwoMeta: 'Field contribution · 8 minutes',
    offlineQueue: 'Sample: 2 observations queued for sync',
    footerNote:
      'Sample data, hypothetical scenarios, and recommendations are never the same thing.',
  },
} as const;

const metrics = {
  fa: [
    {
      label: 'آب قابل دسترس',
      value: '۶۸٪',
      change: '+۴٫۲٪',
      state: 'پایدار',
      icon: 'water',
      accent: 'var(--water)',
    },
    {
      label: 'سلامت خاک',
      value: '۷۴٪',
      change: '+۲٫۱٪',
      state: 'پایدار',
      icon: 'leaf',
      accent: 'var(--forest)',
    },
    {
      label: 'ریسک اقلیم',
      value: 'متوسط',
      change: '۰٫۳↓',
      state: 'پایش',
      icon: 'globe',
      accent: 'var(--copper)',
    },
    {
      label: 'تنوع زیستی',
      value: '۸۱٪',
      change: '+۵٫۸٪',
      state: 'پایدار',
      icon: 'spark',
      accent: 'var(--moss)',
    },
  ],
  en: [
    {
      label: 'Water availability',
      value: '68%',
      change: '+4.2%',
      state: 'Stable',
      icon: 'water',
      accent: 'var(--water)',
    },
    {
      label: 'Soil health',
      value: '74%',
      change: '+2.1%',
      state: 'Stable',
      icon: 'leaf',
      accent: 'var(--forest)',
    },
    {
      label: 'Climate risk',
      value: 'Medium',
      change: '−0.3',
      state: 'Monitor',
      icon: 'globe',
      accent: 'var(--copper)',
    },
    {
      label: 'Biodiversity',
      value: '81%',
      change: '+5.8%',
      state: 'Stable',
      icon: 'spark',
      accent: 'var(--moss)',
    },
  ],
} as const;

const layers = {
  fa: {
    water: { value: '۶۸٪ ظرفیت', detail: 'رطوبت و منابع آب', color: 'var(--water)' },
    soil: { value: '۷۴٪ سلامت', detail: 'مواد آلی و ساختار', color: 'var(--forest)' },
    biodiversity: { value: '۸۱٪ پایداری', detail: 'پوشش و شکل زیستی', color: 'var(--moss)' },
  },
  en: {
    water: {
      value: '68% capacity',
      detail: 'Moisture and water availability',
      color: 'var(--water)',
    },
    soil: { value: '74% health', detail: 'Organic matter and structure', color: 'var(--forest)' },
    biodiversity: {
      value: '81% resilience',
      detail: 'Cover and ecological form',
      color: 'var(--moss)',
    },
  },
} as const;

function Icon({ name, className = 'size-5' }: { name: IconName; className?: string }) {
  const common = {
    className,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    viewBox: '0 0 24 24',
    'aria-hidden': true,
  };

  if (name === 'home') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="m4 10 8-6 8 6v9a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" />
      </svg>
    );
  }
  if (name === 'map') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="m4 6 5-2 6 2 5-2v14l-5 2-6-2-5 2z" />
        <path d="M9 4v14M15 6v14" />
      </svg>
    );
  }
  if (name === 'spark') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z" />
        <path d="m18.5 15 .7 2.3 2.3.7-2.3.7-.7 2.3-.7-2.3-2.3-.7 2.3-.7z" />
      </svg>
    );
  }
  if (name === 'report') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="M6 3h8l4 4v14H6z" />
        <path d="M14 3v5h5M9 12h6M9 16h6" />
      </svg>
    );
  }
  if (name === 'water') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="M12 3s6 6.2 6 11a6 6 0 0 1-12 0c0-4.8 6-11 6-11Z" />
        <path d="M9 15.5a3 3 0 0 0 3 2" />
      </svg>
    );
  }
  if (name === 'leaf') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="M20 4C12 4 5 8 5 15c0 3 2 5 5 5 7 0 10-8 10-16Z" />
        <path d="M4 21c3-5 7-8 12-10" />
      </svg>
    );
  }
  if (name === 'globe') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
      </svg>
    );
  }
  if (name === 'database') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
      </svg>
    );
  }
  if (name === 'sun') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    );
  }
  if (name === 'moon') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z" />
      </svg>
    );
  }
  if (name === 'arrow') {
    return (
      <svg {...common}>
        <title>{name}</title>
        <path d="M5 12h14M14 7l5 5-5 5" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <title>{name}</title>
      <path d="m5 12 4 4L19 6" />
    </svg>
  );
}

function Wordmark() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid size-10 place-items-center rounded-[14px] border border-[var(--line-strong)] bg-[var(--surface)] shadow-[var(--shadow-card)]">
        <span className="absolute size-5 rounded-full border border-[var(--forest)]" />
        <span className="absolute h-px w-7 rotate-[-24deg] bg-[var(--water)]" />
        <span className="absolute h-px w-5 rotate-[28deg] bg-[var(--copper)]" />
      </div>
      <div>
        <div className="font-semibold tracking-[-0.02em] text-[var(--ink)]">Eco Nojin</div>
        <div className="text-[0.65rem] text-[var(--ink-soft)]">Living intelligence</div>
      </div>
    </div>
  );
}

function Panel({
  children,
  className = '',
  style,
  id,
}: {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  id?: string;
}) {
  return (
    <section id={id} className={`card p-5 sm:p-6 ${className}`} style={style}>
      {children}
    </section>
  );
}

function StatusPill({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'good' | 'watch';
}) {
  const tones = {
    neutral: 'border-[var(--line)] bg-[var(--surface-2)] text-[var(--ink-soft)]',
    good: 'border-[color-mix(in_oklch,var(--moss)_42%,var(--line))] bg-[color-mix(in_oklch,var(--moss)_12%,var(--surface))] text-[var(--ink)]',
    watch:
      'border-[color-mix(in_oklch,var(--copper)_48%,var(--line))] bg-[color-mix(in_oklch,var(--copper)_12%,var(--surface))] text-[var(--ink)]',
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.68rem] font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

function FieldMap({
  activeLayer,
  layerCopy,
  prototypeLabel,
  sampleLabel,
}: {
  activeLayer: LayerId;
  layerCopy: (typeof layers)['en'] | (typeof layers)['fa'];
  prototypeLabel: string;
  sampleLabel: string;
}) {
  const active = layerCopy[activeLayer];
  return (
    <Panel className="relative overflow-hidden p-0">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--line)] p-5 sm:p-6">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="status-dot" />
            <span className="text-xs font-semibold text-[var(--ink-soft)]">
              {prototypeLabel} · {sampleLabel}
            </span>
          </div>
          <h2 className="text-xl font-semibold tracking-[-0.02em] text-[var(--ink)]">
            {active.detail}
          </h2>
          <p className="mt-1 text-sm text-[var(--ink-soft)]">{active.value}</p>
        </div>
        <StatusPill tone="watch">
          {activeLayer === 'water' ? '12%' : activeLayer === 'soil' ? '8%' : '15%'}
        </StatusPill>
      </div>
      <div className="relative min-h-[360px] overflow-hidden bg-[var(--surface-2)] sm:min-h-[440px]">
        <svg
          viewBox="0 0 900 520"
          className="absolute inset-0 h-full w-full"
          role="img"
          aria-label={active.detail}
        >
          <rect width="900" height="520" fill="var(--surface-2)" />
          <path
            d="M-20 370C120 300 190 430 330 350S580 180 920 260"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".45"
          />
          <path
            d="M-20 340C140 260 210 390 350 310S610 140 920 220"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".38"
          />
          <path
            d="M-20 310C150 220 230 340 380 265S650 100 920 180"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".32"
          />
          <path
            d="M-20 400C130 340 220 450 360 385S590 220 920 300"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".28"
          />
          <path
            d="M80 100C180 50 280 90 340 180S490 300 570 210 700 70 840 130"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".3"
          />
          <path
            d="M60 140C170 90 260 130 310 220S450 360 550 260 710 120 850 170"
            fill="none"
            stroke="var(--line-strong)"
            strokeWidth="1.2"
            opacity=".24"
          />
          <path
            d="M120 250 245 145l142 55 92-62 156 96-38 128-145 71-176-35-102-88Z"
            fill={active.color}
            fillOpacity=".1"
            stroke={active.color}
            strokeWidth="1.5"
          />
          <path
            d="M245 145 322 278l160-44M322 278l115 155M322 278 213 268M437 234l160 0M120 250l93 18"
            fill="none"
            stroke={active.color}
            strokeOpacity=".5"
            strokeWidth="1"
          />
          <path
            d="M190 390C280 330 360 360 430 300S590 190 720 240"
            fill="none"
            stroke="var(--water)"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M190 390C280 330 360 360 430 300S590 190 720 240L720 270C600 225 530 350 430 340S280 420 190 430Z"
            fill="var(--water)"
            fillOpacity=".09"
          />
          {[
            [190, 390],
            [430, 300],
            [600, 225],
            [720, 240],
          ].map(([cx, cy]) => (
            <g key={`${cx}-${cy}`}>
              <circle cx={cx} cy={cy} r="12" fill={active.color} fillOpacity=".13" />
              <circle cx={cx} cy={cy} r="4" fill={active.color} />
            </g>
          ))}
          <g transform="translate(650 105)">
            <rect
              width="150"
              height="64"
              rx="16"
              fill="var(--surface)"
              stroke="var(--line-strong)"
            />
            <text x="18" y="26" fill="var(--ink-soft)" fontSize="11">
              SAMPLE
            </text>
            <text x="18" y="47" fill="var(--ink)" fontSize="18" fontWeight="700">
              DEMO
            </text>
          </g>
        </svg>
        <div className="absolute bottom-4 start-4 flex flex-wrap gap-2">
          <StatusPill>
            <Icon name="database" className="size-3.5" /> {active.value}
          </StatusPill>
          <StatusPill>
            <Icon name="check" className="size-3.5" /> {sampleLabel}
          </StatusPill>
        </div>
      </div>
    </Panel>
  );
}

export function SustainabilityDashboardPrototype({ locale }: { locale: string }) {
  const language = locale === 'fa' ? 'fa' : 'en';
  const text = copy[language];
  const direction = language === 'fa' ? 'rtl' : 'ltr';
  const [theme, setTheme] = useState<Theme>('dark');
  const [activeLayer, setActiveLayer] = useState<LayerId>('water');
  const [scenario, setScenario] = useState<ScenarioId>('balanced');
  const [activeGoal, setActiveGoal] = useState(6);
  const navTargets = ['live-overview', 'regional-pulse', 'impact-path', 'action-queue'] as const;
  const scrollToSection = (id: string) => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.getElementById(id)?.scrollIntoView({
      behavior: reducedMotion ? 'auto' : 'smooth',
      block: 'start',
    });
  };

  const scenarioValues =
    language === 'fa'
      ? scenario === 'balanced'
        ? { water: '−۹٪', yield: '+۶٪', risk: '۰٫۲↓' }
        : { water: '−۱۵٪', yield: '+۱۱٪', risk: '۰٫۱↓' }
      : scenario === 'balanced'
        ? { water: '−9%', yield: '+6%', risk: '−0.2' }
        : { water: '−15%', yield: '+11%', risk: '−0.1' };

  const goalData = [
    {
      id: 2,
      label: language === 'fa' ? 'تغذیه' : 'Nutrition',
      color: 'var(--forest)',
      value: language === 'fa' ? 'پایداری محصول' : 'Crop resilience',
    },
    {
      id: 6,
      label: language === 'fa' ? 'آب' : 'Water',
      color: 'var(--water)',
      value: language === 'fa' ? 'ظرفیت منابع' : 'Resource capacity',
    },
    {
      id: 13,
      label: language === 'fa' ? 'اقلیم' : 'Climate',
      color: 'var(--copper)',
      value: language === 'fa' ? 'ریسک و سازگاری' : 'Risk and resilience',
    },
    {
      id: 15,
      label: language === 'fa' ? 'زمین' : 'Land',
      color: 'var(--moss)',
      value: language === 'fa' ? 'تنوع زیستی' : 'Biodiversity',
    },
  ] as const;

  const selectedGoal = goalData.find((goal) => goal.id === activeGoal) ?? goalData[1];
  const selectedMetric = metrics[language];
  const stepLabels = [text.observe, text.interpret, text.act, text.evaluate];
  const stepDetails = [
    text.observeDetail,
    text.interpretDetail,
    text.actDetail,
    text.evaluateDetail,
  ];

  return (
    <main
      dir={direction}
      lang={language === 'fa' ? 'fa-IR' : 'en'}
      data-theme={theme}
      style={{ colorScheme: theme }}
      className="min-h-dvh bg-[var(--canvas)] text-[var(--ink)]"
    >
      <div
        className="pointer-events-none fixed inset-0 opacity-70"
        style={{
          backgroundImage:
            'radial-gradient(circle at 12% 4%, color-mix(in oklch, var(--water) 18%, transparent), transparent 28%), radial-gradient(circle at 88% 12%, color-mix(in oklch, var(--forest) 15%, transparent), transparent 30%)',
        }}
      />
      <div className="relative mx-auto grid min-h-dvh max-w-[1600px] lg:grid-cols-[17rem_minmax(0,1fr)]">
        <aside className="sticky top-0 hidden h-dvh flex-col border-e border-[var(--line)] bg-[color-mix(in_oklch,var(--canvas)_88%,transparent)] p-5 backdrop-blur-xl lg:flex">
          <Wordmark />
          <div className="mt-10">
            <div className="mb-3 text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-[var(--ink-soft)]">
              {text.prototype}
            </div>
            <nav className="space-y-2" aria-label={text.overview}>
              {(['home', 'map', 'spark', 'report'] as IconName[]).map((icon, index) => (
                <button
                  key={icon}
                  type="button"
                  aria-current={index === 0 ? 'page' : undefined}
                  onClick={() => scrollToSection(navTargets[index])}
                  className="flex w-full items-center gap-3 rounded-2xl border border-transparent px-3 py-2.5 text-start text-sm font-medium text-[var(--ink-soft)] transition hover:border-[var(--line)] hover:bg-[var(--surface)] hover:text-[var(--ink)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
                >
                  <Icon name={icon} className="size-4.5" />
                  {text.navigation[index]}
                  {index === 0 ? (
                    <span className="ms-auto size-1.5 rounded-full bg-[var(--forest)]" />
                  ) : null}
                </button>
              ))}
            </nav>
          </div>
          <div className="mt-auto rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="text-xs font-semibold text-[var(--ink)]">{text.lastSync}</span>
              <span className="text-[0.65rem] text-[var(--ink-soft)]">{text.minutes}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-[var(--surface-2)]">
              <div className="h-full w-[82%] rounded-full bg-[var(--forest)]" />
            </div>
            <div className="mt-3 flex items-center gap-2 text-[0.68rem] text-[var(--ink-soft)]">
              <span className="status-dot" />
              {text.offlineQueue}
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between px-2 text-[0.65rem] text-[var(--ink-soft)]">
            <span>{text.localeName}</span>
            <button
              type="button"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="grid size-9 place-items-center rounded-xl border border-[var(--line)] bg-[var(--surface)] transition hover:border-[var(--line-strong)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
              aria-label={theme === 'dark' ? 'Use light theme' : 'Use dark theme'}
            >
              <Icon name={theme === 'dark' ? 'sun' : 'moon'} className="size-4" />
            </button>
          </div>
        </aside>

        <div className="min-w-0 pb-24 lg:pb-8">
          <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-[var(--line)] bg-[color-mix(in_oklch,var(--canvas)_84%,transparent)] px-4 backdrop-blur-xl sm:px-6 lg:px-8">
            <div className="lg:hidden">
              <Wordmark />
            </div>
            <div className="hidden items-center gap-2 lg:flex">
              <span className="text-sm font-semibold">{text.overview}</span>
              <span className="text-[var(--ink-soft)]">/</span>
              <span className="text-sm text-[var(--ink-soft)]">{text.location}</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusPill tone="good">
                <span className="status-dot" /> {text.synced}
              </StatusPill>
              <button
                type="button"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="grid size-9 place-items-center rounded-xl border border-[var(--line)] bg-[var(--surface)] lg:hidden"
                aria-label={theme === 'dark' ? 'Use light theme' : 'Use dark theme'}
              >
                <Icon name={theme === 'dark' ? 'sun' : 'moon'} className="size-4" />
              </button>
              <div className="grid size-9 place-items-center rounded-xl bg-[var(--forest)] text-xs font-bold text-[var(--on-action)]">
                EN
              </div>
            </div>
          </header>

          <div className="space-y-6 p-4 sm:p-6 lg:p-8">
            <section
              id="live-overview"
              className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(22rem,0.75fr)]"
            >
              <div className="relative overflow-hidden rounded-[2rem] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-[var(--shadow-card)] sm:p-8 lg:p-10">
                <div className="absolute inset-0 contour opacity-70" />
                <div className="absolute -end-20 -top-24 size-72 rounded-full border border-[color-mix(in_oklch,var(--water)_28%,transparent)] bg-[color-mix(in_oklch,var(--water)_8%,transparent)] blur-2xl" />
                <div className="relative flex min-h-[440px] flex-col justify-between">
                  <div>
                    <StatusPill tone="good">{text.eyebrow}</StatusPill>
                    <h1 className="mt-6 max-w-[18ch] text-balance text-[clamp(2.4rem,6vw,5.6rem)] font-semibold leading-[1.03] tracking-[-0.055em] text-[var(--ink)]">
                      {text.title}
                    </h1>
                    <p className="mt-5 max-w-[58ch] text-sm leading-7 text-[var(--ink-soft)] sm:text-base">
                      {text.description}
                    </p>
                    <div className="mt-7 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => scrollToSection('regional-pulse')}
                        className="btn btn-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
                      >
                        {text.primaryCta} <Icon name="arrow" className="size-4 rtl:rotate-180" />
                      </button>
                      <button
                        type="button"
                        onClick={() => scrollToSection('scenario')}
                        className="btn btn-ghost focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
                      >
                        {text.secondaryCta}
                      </button>
                    </div>
                  </div>
                  <div className="mt-10 grid grid-cols-3 gap-3 border-t border-[var(--line)] pt-6">
                    {[
                      ['۱۲', text.coverage],
                      ['۳۸', text.stations],
                      ['۱۴', text.lastSync],
                    ].map(([value, label]) => (
                      <div key={label}>
                        <div className="num text-2xl font-semibold text-[var(--ink)]">{value}</div>
                        <div className="mt-1 text-[0.68rem] text-[var(--ink-soft)] sm:text-xs">
                          {label}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <FieldMap
                activeLayer={activeLayer}
                layerCopy={layers[language]}
                prototypeLabel={text.prototype}
                sampleLabel={text.sampleData}
              />
            </section>

            <Panel id="regional-pulse">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold tracking-[-0.02em]">{text.pulse}</h2>
                  <p className="mt-1 text-sm text-[var(--ink-soft)]">{text.pulseDescription}</p>
                </div>
                <fieldset className="flex flex-wrap gap-2">
                  <legend className="sr-only">{text.layer}</legend>
                  {(['water', 'soil', 'biodiversity'] as LayerId[]).map((layer) => (
                    <button
                      key={layer}
                      type="button"
                      aria-pressed={activeLayer === layer}
                      onClick={() => setActiveLayer(layer)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)] ${activeLayer === layer ? 'border-[var(--forest)] bg-[color-mix(in_oklch,var(--forest)_14%,var(--surface))] text-[var(--ink)]' : 'border-[var(--line)] bg-[var(--surface-2)] text-[var(--ink-soft)] hover:border-[var(--line-strong)]'}`}
                    >
                      {text[layer]}
                    </button>
                  ))}
                </fieldset>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {selectedMetric.map((metric) => (
                  <article
                    key={metric.label}
                    className="group rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-4 transition hover:-translate-y-0.5 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow-card)]"
                    style={{ '--metric-accent': metric.accent } as CSSProperties}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="grid size-9 place-items-center rounded-xl bg-[var(--surface)] text-[var(--metric-accent)]">
                        <Icon name={metric.icon as IconName} className="size-4.5" />
                      </span>
                      <span className="num text-xs font-semibold text-[var(--ink-soft)]">
                        {metric.change}
                      </span>
                    </div>
                    <div className="num mt-5 text-2xl font-semibold text-[var(--ink)]">
                      {metric.value}
                    </div>
                    <div className="mt-1 text-xs font-medium text-[var(--ink-soft)]">
                      {metric.label}
                    </div>
                    <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--surface)]">
                      <div className="h-full w-[72%] rounded-full bg-[var(--metric-accent)] transition-[width] duration-500 ease-out-quart group-hover:w-[78%]" />
                    </div>
                  </article>
                ))}
              </div>
            </Panel>

            <section
              id="impact-path"
              className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.65fr)]"
            >
              <Panel>
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold tracking-[-0.02em]">{text.impactPath}</h2>
                    <p className="mt-1 text-sm text-[var(--ink-soft)]">
                      {text.impactPathDescription}
                    </p>
                  </div>
                  <StatusPill>
                    <Icon name="check" className="size-3.5" /> {text.illustrative}
                  </StatusPill>
                </div>
                <ol className="mt-7 grid gap-4 sm:grid-cols-2">
                  {stepLabels.map((label, index) => (
                    <li
                      key={label}
                      className="relative rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-4"
                    >
                      <div className="flex items-center gap-3">
                        <span className="num grid size-8 place-items-center rounded-full bg-[var(--forest)] text-xs font-bold text-[var(--on-action)]">
                          {index + 1}
                        </span>
                        <div>
                          <div className="text-sm font-semibold">{label}</div>
                          <div className="mt-1 text-xs text-[var(--ink-soft)]">
                            {stepDetails[index]}
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </Panel>

              <Panel>
                <div>
                  <StatusPill tone="good">{text.domainLabel}</StatusPill>
                  <h2 className="mt-4 text-xl font-semibold tracking-[-0.02em]">
                    {text.impactLens}
                  </h2>
                  <p className="mt-1 text-sm text-[var(--ink-soft)]">{text.impactDescription}</p>
                </div>
                <fieldset className="mt-5 min-w-0 space-y-2">
                  <legend className="sr-only">{text.impactLens}</legend>
                  {goalData.map((goal) => (
                    <button
                      key={goal.id}
                      type="button"
                      aria-pressed={activeGoal === goal.id}
                      onClick={() => setActiveGoal(goal.id)}
                      className={`flex w-full items-center gap-3 rounded-2xl border p-3 text-start transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)] ${activeGoal === goal.id ? 'border-[var(--line-strong)] bg-[var(--surface-2)]' : 'border-transparent hover:border-[var(--line)]'}`}
                    >
                      <span
                        className="num grid size-9 place-items-center rounded-xl text-sm font-bold text-[var(--on-action)]"
                        style={{ backgroundColor: goal.color }}
                      >
                        {goal.id}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold">{goal.label}</span>
                        <span className="mt-0.5 block text-xs text-[var(--ink-soft)]">
                          {goal.value}
                        </span>
                      </span>
                      <span
                        className={`size-2 rounded-full ${activeGoal === goal.id ? 'bg-[var(--forest)]' : 'bg-[var(--line-strong)]'}`}
                      />
                    </button>
                  ))}
                </fieldset>
                <div className="mt-4 flex flex-wrap gap-2">
                  <StatusPill>{text.global}</StatusPill>
                  <StatusPill tone="watch">{text.localProxy}</StatusPill>
                </div>
                <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-4">
                  <div className="text-xs text-[var(--ink-soft)]">{text.selectedGoal}</div>
                  <div className="mt-1 flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold">
                      {text.impactPrefix} {selectedGoal.id} · {selectedGoal.label}
                    </span>
                    <span
                      className="size-2.5 rounded-full"
                      style={{ backgroundColor: selectedGoal.color }}
                    />
                  </div>
                </div>
              </Panel>
            </section>

            <section id="scenario" className="grid gap-5 lg:grid-cols-3">
              <Panel className="lg:col-span-2">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <StatusPill tone="watch">AI SCENARIO</StatusPill>
                    <h2 className="mt-4 text-xl font-semibold tracking-[-0.02em]">
                      {text.scenario}
                    </h2>
                    <p className="mt-1 text-sm text-[var(--ink-soft)]">
                      {text.scenarioDescription}
                    </p>
                  </div>
                  <fieldset className="flex rounded-full border border-[var(--line)] bg-[var(--surface-2)] p-1">
                    <legend className="sr-only">{text.scenario}</legend>
                    {(['balanced', 'accelerated'] as ScenarioId[]).map((item) => (
                      <button
                        key={item}
                        type="button"
                        aria-pressed={scenario === item}
                        onClick={() => setScenario(item)}
                        className={`rounded-full px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)] ${scenario === item ? 'bg-[var(--surface)] text-[var(--ink)] shadow-[var(--shadow-card)]' : 'text-[var(--ink-soft)]'}`}
                      >
                        {text[item]}
                      </button>
                    ))}
                  </fieldset>
                </div>
                <div className="mt-7 grid gap-3 sm:grid-cols-3">
                  {[
                    [text.scenarioResult, scenarioValues.water, 'var(--water)'],
                    [text.scenarioYield, scenarioValues.yield, 'var(--forest)'],
                    [text.scenarioRisk, scenarioValues.risk, 'var(--copper)'],
                  ].map(([label, value, color]) => (
                    <div
                      key={label}
                      className="rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-4"
                      style={{ '--scenario-color': color } as CSSProperties}
                    >
                      <div className="text-xs text-[var(--ink-soft)]">{label}</div>
                      <div
                        className="num mt-2 text-2xl font-semibold"
                        style={{ color: 'var(--scenario-color)' }}
                      >
                        {value}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex items-start gap-2 rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-3 text-xs text-[var(--ink-soft)]">
                  <Icon name="spark" className="mt-0.5 size-4 shrink-0 text-[var(--copper)]" />
                  {text.scenarioModel}
                </div>
              </Panel>

              <Panel>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold tracking-[-0.02em]">{text.evidence}</h2>
                    <p className="mt-1 text-sm text-[var(--ink-soft)]">
                      {text.impactPathDescription}
                    </p>
                  </div>
                  <span className="grid size-10 place-items-center rounded-xl bg-[var(--surface-2)] text-[var(--water)]">
                    <Icon name="database" />
                  </span>
                </div>
                <dl className="mt-6 divide-y divide-[var(--line)]">
                  {[
                    [text.source, text.sourceValue],
                    [text.method, text.methodValue],
                    [text.coverageLabel, text.coverageValue],
                    [text.freshness, text.freshnessValue],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                    >
                      <dt className="text-xs text-[var(--ink-soft)]">{label}</dt>
                      <dd className="text-end text-xs font-semibold text-[var(--ink)]">{value}</dd>
                    </div>
                  ))}
                </dl>
              </Panel>
            </section>

            <section
              id="action-queue"
              className="grid gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(20rem,0.75fr)]"
            >
              <Panel>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold tracking-[-0.02em]">{text.actionQueue}</h2>
                    <p className="mt-1 text-sm text-[var(--ink-soft)]">{text.footerNote}</p>
                  </div>
                  <span className="num text-2xl font-semibold">۲</span>
                </div>
                <div className="mt-6 space-y-3">
                  {[
                    [text.actionOne, text.actionOneMeta, '01'],
                    [text.actionTwo, text.actionTwoMeta, '02'],
                  ].map(([title, meta, index]) => (
                    <article
                      key={title}
                      className="group flex w-full items-center gap-4 rounded-2xl border border-[var(--line)] bg-[var(--surface-2)] p-4 text-start"
                    >
                      <span className="num grid size-10 shrink-0 place-items-center rounded-xl border border-[var(--line)] text-xs font-semibold">
                        {index}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold">{title}</span>
                        <span className="mt-1 block text-xs text-[var(--ink-soft)]">{meta}</span>
                      </span>
                      <Icon
                        name="arrow"
                        className="size-4 shrink-0 text-[var(--ink-soft)] transition-transform group-hover:translate-x-0.5 rtl:rotate-180 rtl:group-hover:-translate-x-0.5"
                      />
                    </article>
                  ))}
                </div>
              </Panel>

              <Panel className="flex flex-col justify-between overflow-hidden">
                <div>
                  <StatusPill tone="good">
                    <span className="status-dot" /> {text.synced}
                  </StatusPill>
                  <h2 className="mt-4 text-xl font-semibold tracking-[-0.02em]">{text.lastSync}</h2>
                  <div className="num mt-3 text-5xl font-semibold tracking-[-0.05em]">14</div>
                  <p className="mt-1 text-sm text-[var(--ink-soft)]">{text.minutes}</p>
                </div>
                <div className="relative mt-8 h-32 overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--surface-2)]">
                  <div className="absolute inset-0 contour opacity-60" />
                  <svg
                    viewBox="0 0 360 128"
                    className="absolute inset-0 h-full w-full"
                    aria-hidden="true"
                  >
                    <path
                      d="M-10 90C45 74 78 102 124 72s86-30 124-8 79 0 122-31"
                      fill="none"
                      stroke="var(--forest)"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                    <path
                      d="M-10 90C45 74 78 102 124 72s86-30 124-8 79 0 122-31V140H-10Z"
                      fill="var(--forest)"
                      fillOpacity=".08"
                    />
                  </svg>
                </div>
              </Panel>
            </section>
          </div>
        </div>
      </div>

      <nav
        className="fixed inset-x-3 bottom-3 z-50 grid grid-cols-4 rounded-2xl border border-[var(--line-strong)] bg-[color-mix(in_oklch,var(--surface)_90%,transparent)] p-1.5 shadow-[var(--shadow-card)] backdrop-blur-xl lg:hidden"
        aria-label={text.overview}
      >
        {(['home', 'map', 'spark', 'report'] as IconName[]).map((icon, index) => (
          <button
            key={icon}
            type="button"
            aria-current={index === 0 ? 'page' : undefined}
            className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-xl text-[0.62rem] font-semibold focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[var(--water)] ${index === 0 ? 'bg-[var(--surface-2)] text-[var(--ink)]' : 'text-[var(--ink-soft)]'}`}
          >
            <Icon name={icon} className="size-4" />
            {text.navigation[index]}
          </button>
        ))}
      </nav>
    </main>
  );
}
