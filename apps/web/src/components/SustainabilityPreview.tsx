'use client';

import { type CSSProperties, useState } from 'react';

type PreviewLayer = 'water' | 'soil' | 'nature';

export type SustainabilityPreviewData = {
  source: 'live' | 'fallback';
  landscapes: number | null;
  projects: number | null;
};

type PreviewCopy = {
  eyebrow: string;
  title: string;
  lead: string;
  sample: string;
  live: string;
  fallback: string;
  platformCounts: string;
  landscapes: string;
  projects: string;
  sourceLive: string;
  signalNote: string;
  view: string;
  layerLabel: string;
  pathTitle: string;
  pathLead: string;
  evidenceTitle: string;
  evidenceLead: string;
  observe: string;
  interpret: string;
  act: string;
  evaluate: string;
  source: string;
  method: string;
  scope: string;
  freshness: string;
  sourceValue: string;
  methodValue: string;
  scopeValue: string;
  freshnessValue: string;
  pathLink: string;
  note: string;
  layers: Record<
    PreviewLayer,
    { label: string; value: string; detail: string; color: string; change: string }
  >;
};

const previewCopy: Record<'fa' | 'en', PreviewCopy> = {
  fa: {
    eyebrow: 'پیش‌نمایش مسیر پایدار',
    title: 'اثر را از داده و شواهد جدا کن',
    lead: 'یک نمای فشرده از مشاهده، تفسیر، اقدام و سنجش؛ با دادهٔ نمونه و مرزهای روشن.',
    sample: 'دادهٔ نمونه',
    live: 'دادهٔ پلتفرم',
    fallback: 'اتصال زنده در دسترس نیست',
    platformCounts: 'شمارش پلتفرم',
    landscapes: 'پروفایل زمین',
    projects: 'پروژه',
    sourceLive: 'Platform Stats API',
    signalNote: 'کارت‌های آب، خاک و تنوع زیستی در این پیش‌نمایش نمونه‌اند.',
    view: 'باز کردن نمونهٔ تعاملی',
    layerLabel: 'لایهٔ نمونه',
    pathTitle: 'مسیر اثر',
    pathLead: 'هر سیگنال باید به فهم، اقدام و بازخورد برسد.',
    evidenceTitle: 'شواهد و مرزها',
    evidenceLead: 'عدد نمایشی، منبع و روش خودش را دارد.',
    observe: 'مشاهده',
    interpret: 'تفسیر',
    act: 'اقدام',
    evaluate: 'سنجش',
    source: 'منبع',
    method: 'روش',
    scope: 'دامنه',
    freshness: 'تازگی',
    sourceValue: 'دادهٔ نمایشی',
    methodValue: 'قرارداد پیش‌نمایش',
    scopeValue: 'منطقهٔ نمونه',
    freshnessValue: 'شبیه‌سازی‌شده',
    pathLink: 'ورود به Prototype',
    note: 'دادهٔ واقعی، سناریوی فرضی و پیشنهاد مدیریتی یکی نیستند.',
    layers: {
      water: {
        label: 'آب',
        value: '۶۸٪',
        detail: 'ظرفیت و رطوبت',
        color: 'var(--water)',
        change: '+۴٫۲٪',
      },
      soil: {
        label: 'خاک',
        value: '۷۴٪',
        detail: 'مادهٔ آلی و ساختار',
        color: 'var(--forest)',
        change: '+۲٫۱٪',
      },
      nature: {
        label: 'تنوع زیستی',
        value: '۸۱٪',
        detail: 'پوشش و شکل زیستی',
        color: 'var(--moss)',
        change: '+۵٫۸٪',
      },
    },
  },
  en: {
    eyebrow: 'Sustainability preview',
    title: 'Separate impact from evidence',
    lead: 'A compact view of observation, interpretation, action, and evaluation with clear boundaries and illustrative data.',
    sample: 'Sample data',
    live: 'Platform data',
    fallback: 'Live connection unavailable',
    platformCounts: 'Platform counts',
    landscapes: 'Land profiles',
    projects: 'Projects',
    sourceLive: 'Platform Stats API',
    signalNote: 'Water, soil, and biodiversity cards are illustrative in this preview.',
    view: 'Open interactive prototype',
    layerLabel: 'Sample layer',
    pathTitle: 'Impact pathway',
    pathLead: 'Every signal should lead to understanding, action, and feedback.',
    evidenceTitle: 'Evidence and boundaries',
    evidenceLead: 'Every illustrative number carries its source and method.',
    observe: 'Observe',
    interpret: 'Interpret',
    act: 'Act',
    evaluate: 'Evaluate',
    source: 'Source',
    method: 'Method',
    scope: 'Scope',
    freshness: 'Freshness',
    sourceValue: 'Illustrative data',
    methodValue: 'Preview contract',
    scopeValue: 'Sample region',
    freshnessValue: 'Simulated',
    pathLink: 'Enter prototype',
    note: 'Observed data, hypothetical scenarios, and recommendations are not the same thing.',
    layers: {
      water: {
        label: 'Water',
        value: '68%',
        detail: 'Capacity and moisture',
        color: 'var(--water)',
        change: '+4.2%',
      },
      soil: {
        label: 'Soil',
        value: '74%',
        detail: 'Organic matter and structure',
        color: 'var(--forest)',
        change: '+2.1%',
      },
      nature: {
        label: 'Biodiversity',
        value: '81%',
        detail: 'Cover and ecological form',
        color: 'var(--moss)',
        change: '+5.8%',
      },
    },
  },
};

export function SustainabilityPreview({
  locale,
  compact = false,
  data,
}: {
  locale: string;
  compact?: boolean;
  data?: SustainabilityPreviewData;
}) {
  const language = locale === 'fa' ? 'fa' : 'en';
  const text = previewCopy[language];
  const [activeLayer, setActiveLayer] = useState<PreviewLayer>('water');
  const active = text.layers[activeLayer];
  const prototypeHref = `/${locale}/prototype`;
  const path = [text.observe, text.interpret, text.act, text.evaluate];
  const isLive = data?.source === 'live';
  const dataLabel = isLive ? text.live : data ? text.fallback : text.sample;
  const numberFormat = new Intl.NumberFormat(language === 'fa' ? 'fa-IR' : 'en');
  const displayNumber = (value: number | null | undefined) =>
    value == null ? '—' : numberFormat.format(value);

  return (
    <section
      className={`panel relative overflow-hidden ${compact ? 'p-5' : 'p-6 sm:p-8'}`}
      aria-labelledby="impact-preview-title"
    >
      <div className="pointer-events-none absolute inset-0 contour opacity-40" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <span className="chip text-[var(--ink-soft)]">
              <span className="status-dot" aria-hidden="true" />
              {text.eyebrow} · {dataLabel}
            </span>
            <h2
              id="impact-preview-title"
              className={`mt-4 font-semibold tracking-[-0.03em] text-[var(--ink)] ${compact ? 'text-2xl' : 'text-3xl'}`}
            >
              {text.title}
            </h2>
            <p className="mt-2 text-sm leading-6 text-[var(--ink-soft)]">{text.lead}</p>
            {data ? (
              <fieldset className="mt-4 flex flex-wrap items-center gap-2">
                <legend className="sr-only">{text.platformCounts}</legend>
                <span className="chip text-[var(--ink-soft)]">{text.platformCounts}</span>
                {isLive ? (
                  <>
                    <span className="chip">
                      <span className="num">{displayNumber(data.landscapes)}</span>{' '}
                      {text.landscapes}
                    </span>
                    <span className="chip">
                      <span className="num">{displayNumber(data.projects)}</span> {text.projects}
                    </span>
                  </>
                ) : (
                  <span className="text-xs text-[var(--ink-soft)]">{text.fallback}</span>
                )}
              </fieldset>
            ) : null}
          </div>
          <a
            href={prototypeHref}
            className="inline-flex items-center gap-2 rounded-[var(--radius-pill)] border border-[var(--line-strong)] px-4 py-2 text-sm font-semibold text-[var(--ink)] transition hover:border-[var(--water)] hover:text-[var(--water)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
          >
            {text.view}
            <span aria-hidden="true">↗</span>
          </a>
        </div>

        <fieldset className="mt-6 flex flex-wrap gap-2">
          <legend className="sr-only">{text.layerLabel}</legend>
          {(Object.keys(text.layers) as PreviewLayer[]).map((layer) => {
            const item = text.layers[layer];
            return (
              <button
                key={layer}
                type="button"
                aria-label={`${item.label} · ${text.layerLabel}`}
                aria-pressed={activeLayer === layer}
                onClick={() => setActiveLayer(layer)}
                className={`rounded-[var(--radius-pill)] border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)] ${activeLayer === layer ? 'border-[var(--forest)] bg-[color-mix(in_oklch,var(--forest)_14%,var(--surface))] text-[var(--ink)]' : 'border-[var(--line)] bg-[var(--surface)] text-[var(--ink-soft)] hover:border-[var(--line-strong)]'}`}
              >
                {item.label}
              </button>
            );
          })}
        </fieldset>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {(Object.keys(text.layers) as PreviewLayer[]).map((layer) => {
            const item = text.layers[layer];
            const selected = layer === activeLayer;
            return (
              <button
                key={layer}
                type="button"
                onClick={() => setActiveLayer(layer)}
                aria-pressed={selected}
                className={`rounded-[var(--radius-card)] border p-4 text-start transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)] ${selected ? 'border-[var(--line-strong)] bg-[var(--surface-2)] shadow-[var(--shadow-card)]' : 'border-[var(--line)] bg-[var(--surface)] hover:border-[var(--line-strong)]'}`}
                style={{ '--preview-accent': item.color } as CSSProperties}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-[var(--ink-soft)]">{item.label}</span>
                  <span className="num text-xs font-semibold" style={{ color: item.color }}>
                    {item.change}
                  </span>
                </div>
                <div className="num mt-3 text-2xl font-semibold text-[var(--ink)]">
                  {item.value}
                </div>
                <div className="mt-1 text-xs text-[var(--ink-soft)]">{item.detail}</div>
                <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[var(--canvas)]">
                  <div
                    className="h-full rounded-full bg-[var(--preview-accent)]"
                    style={{ width: selected ? '78%' : '52%' }}
                  />
                </div>
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-[var(--ink-soft)]">{text.signalNote}</p>

        <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(16rem,0.75fr)]">
          <div className="rounded-[var(--radius-card)] border border-[var(--line)] bg-[var(--surface-2)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-[var(--ink)]">{text.pathTitle}</h3>
                <p className="mt-1 text-xs text-[var(--ink-soft)]">{text.pathLead}</p>
              </div>
              <span className="text-xs text-[var(--ink-soft)]">{dataLabel}</span>
            </div>
            <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {path.map((step, index) => (
                <li
                  key={step}
                  className="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-xs"
                >
                  <span className="num grid size-5 place-items-center rounded-full bg-[var(--forest)] text-[0.6rem] font-bold text-[var(--on-action)]">
                    {index + 1}
                  </span>
                  <span className="font-medium text-[var(--ink)]">{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-[var(--radius-card)] border border-[var(--line)] bg-[var(--surface-2)] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-[var(--ink)]">{text.evidenceTitle}</h3>
                <p className="mt-1 text-xs text-[var(--ink-soft)]">{text.evidenceLead}</p>
              </div>
              <span className="chip">{active.label}</span>
            </div>
            <dl className="mt-4 space-y-2 text-xs">
              {[
                [text.source, isLive ? text.sourceLive : text.sourceValue],
                [text.method, text.methodValue],
                [text.scope, text.scopeValue],
                [text.freshness, text.freshnessValue],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between gap-3 border-b border-[var(--line)] pb-2 last:border-0 last:pb-0"
                >
                  <dt className="text-[var(--ink-soft)]">{label}</dt>
                  <dd className="text-end font-semibold text-[var(--ink)]">{value}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 text-[0.68rem] leading-5 text-[var(--ink-faint)]">{text.note}</p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-4">
          <span className="text-xs text-[var(--ink-soft)]">{dataLabel}</span>
          <a
            href={prototypeHref}
            className="text-sm font-semibold text-[var(--water)] hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--water)]"
          >
            {text.pathLink}
          </a>
        </div>
      </div>
    </section>
  );
}
