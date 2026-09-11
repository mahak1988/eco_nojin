import { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

type SeriesKey = 'ndvi' | 'ndwi' | 'carbon' | 'water';

interface SeriesConfig {
  key: SeriesKey;
  color: string;
  labelFa: string;
  labelEn: string;
  min: number;
  max: number;
  suffix: string;
  precision: number;
}

const SERIES: Record<SeriesKey, SeriesConfig> = {
  ndvi: {
    key: 'ndvi',
    color: '#2fb36b',
    labelFa: 'NDVI (پوشش گیاشتی)',
    labelEn: 'NDVI (vegetation)',
    min: 0,
    max: 1,
    suffix: '',
    precision: 2,
  },
  ndwi: {
    key: 'ndwi',
    color: '#2a9bb5',
    labelFa: 'NDWI (آب)',
    labelEn: 'NDWI (water)',
    min: 0,
    max: 1,
    suffix: '',
    precision: 2,
  },
  carbon: {
    key: 'carbon',
    color: '#d49b3f',
    labelFa: 'کربن خاک (تن/هکتار)',
    labelEn: 'Soil carbon (t/ha)',
    min: 100,
    max: 240,
    suffix: 't/ha',
    precision: 0,
  },
  water: {
    key: 'water',
    color: '#7fd8e8',
    labelFa: 'صرفه‌جویی آب (م³/ماه)',
    labelEn: 'Water saved (m³/month)',
    min: 300,
    max: 540,
    suffix: 'm³',
    precision: 0,
  },
};

const CHART_WIDTH = 560;
const CHART_HEIGHT = 240;
const PAD = 40;

function toY(v: number, cfg: SeriesConfig): number {
  const range = cfg.max - cfg.min;
  const ratio = (v - cfg.min) / range;
  return CHART_HEIGHT - PAD - ratio * (CHART_HEIGHT - PAD * 2);
}

/** Hand-coded SVG time-series chart with tabs — no external chart library. */
export default function ImpactTimeSeries() {
  const { t, lang } = useLang();
  const reduce = useReducedMotion();
  const [active, setActive] = useState<SeriesKey>('ndvi');

  const ts = t.impact.sampleTimeSeries;
  const cfg = SERIES[active];
  const months = lang === 'fa' ? ts.months : ts.monthsEn;
  const values = ts[active];

  const stepX = (CHART_WIDTH - PAD * 2) / (values.length - 1);
  const points = values.map((v, i) => ({ x: PAD + i * stepX, y: toY(v, cfg) }));
  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const area = `${line} L${points[points.length - 1].x.toFixed(1)} ${CHART_HEIGHT - PAD} L${PAD} ${CHART_HEIGHT - PAD} Z`;

  const tabs = Object.values(SERIES);

  return (
    <section className="px-4 py-12 sm:px-6">
      <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {t.impact.chartsTitle}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {t.impact.chartsNote}
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActive(tab.key)}
              className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
                active === tab.key
                  ? 'ring-glow bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                  : 'glass text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]'
              }}`}
            >
              {lang === 'fa' ? tab.labelFa : tab.labelEn}
            </button>
          ))}
        </div>

        <div className="relative mx-auto h-64 w-full max-w-[560px]">
          <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="w-full" role="img">
            {/* background */}
            <rect x={PAD} y={PAD} width={CHART_WIDTH - PAD * 2} height={CHART_HEIGHT - PAD * 2} fill="#04100b" rx="6" />

            {/* grid lines */}
            {[0.25, 0.5, 0.75].map((f) => {
              const y = toY(cfg.min + f * (cfg.max - cfg.min), cfg);
              return (
                <line
                  key={f}
                  x1={PAD}
                  x2={CHART_WIDTH - PAD}
                  y1={y}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeDasharray="3 5"
                />
              );
            })}

            {/* area fill */}
            <defs>
              <linearGradient id={`grad-${cfg.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={cfg.color} stopOpacity="0.4" />
                <stop offset="100%" stopColor={cfg.color} stopOpacity="0" />
              </linearGradient>
            </defs>
            {reduce ? null : (
              <motion.path
                d={area}
                fill={`url(#grad-${cfg.key})`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.4 }}
              />
            )}

            {/* main line */}
            {reduce ? (
              <path d={line} fill="none" stroke={cfg.color} strokeWidth="2.5" strokeLinecap="round" />
            ) : (
              <motion.path
                d={line}
                fill="none"
                stroke={cfg.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.6, ease: 'easeInOut', delay: 0.5 }}
              />
            )}

            {/* data points */}
            {points.map((p, i) => (
              <motion.circle
                key={i}
                cx={p.x}
                cy={p.y}
                r="3.5"
                fill="#04100b"
                stroke={cfg.color}
                strokeWidth="2"
                initial={reduce ? undefined : { opacity: 0 }}
                animate={reduce ? undefined : { opacity: 1 }}
                transition={{ delay: 0.5 + i * 0.08 }}
              />
            ))}

            {/* axis labels */}
            {months.map((m, i) => (
              <text
                key={m + i}
                x={PAD + i * stepX}
                y={CHART_HEIGHT - 8}
                textAnchor="middle"
                fontSize="9"
                fill="rgba(230,242,234,0.3)"
              >
                {m}
              </text>
            ))}
          </svg>

          {/* live badge */}
          <span className="absolute top-2 end-2 rounded-full bg-[var(--color-sand-500)]/20 px-2 py-0.5 text-[10px] font-bold text-[var(--color-sand-300)]">
            {lang === 'fa' ? 'نمونه' : 'Sample'}
          </span>
        </div>

        <p className="text-center text-[10px] text-[var(--color-night-200)]/35">
          {lang === 'fa'
            ? 'نمونهٔ تصویری — دادهٔ واقعی هنگام وصل شدن به API ماهواره‌ای منتشر می‌شود.'
            : 'Illustrative sample — real data goes live once the satellite API is connected.'}
        </p>
      </Reveal>
    </section>
  );
}
