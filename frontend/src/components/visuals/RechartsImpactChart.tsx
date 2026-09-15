import { useState, useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import type { Lang } from '../../content/site';

type SeriesKey = 'ndvi' | 'ndwi' | 'carbon' | 'water';

interface SeriesConfig {
  key: SeriesKey;
  color: string;
  labelFa: string;
  labelEn: string;
}

const SERIES: Record<SeriesKey, SeriesConfig> = {
  ndvi: { key: 'ndvi', color: '#2fb36b', labelFa: 'NDVI (پوشش گیاشتی)', labelEn: 'NDVI (vegetation)' },
  ndwi: { key: 'ndwi', color: '#2a9bb5', labelFa: 'NDWI (آب)', labelEn: 'NDWI (water)' },
  carbon: { key: 'carbon', color: '#d49b3f', labelFa: 'کربن خاک (تن/هکتار)', labelEn: 'Soil carbon (t/ha)' },
  water: { key: 'water', color: '#7fd8e8', labelFa: 'صرفه‌جویی آب (م³/ماه)', labelEn: 'Water saved (m³/month)' },
};

interface RechartsImpactChartProps {
  months: string[];
  monthsEn: string[];
  ndvi: number[];
  ndwi: number[];
  carbon: number[];
  water: number[];
  className?: string;
}

function buildChartData(
  props: RechartsImpactChartProps,
  lang: Lang,
) {
  const months = lang === 'fa' ? props.months : props.monthsEn;
  return props.ndvi.map((_, i) => ({
    label: months[i] ?? '',
    ndvi: props.ndvi[i],
    ndwi: props.ndwi[i],
    carbon: props.carbon[i],
    water: props.water[i],
  }));
}

const AreaChartRaw = AreaChart as any;
const AreaRaw = Area as any;
const XAxisRaw = XAxis as any;
const YAxisRaw = YAxis as any;
const CartesianGridRaw = CartesianGrid as any;
const TooltipRaw = Tooltip as any;
const ResponsiveContainerRaw = ResponsiveContainer as any;
const LegendRaw = Legend as any;

export default function RechartsImpactChart({
  data,
  className,
}: {
  data: RechartsImpactChartProps;
  className?: string;
}) {
  const { lang } = useLang();
  const [active, setActive] = useState<SeriesKey>('ndvi');
  const cfg = SERIES[active];

  const chartData = useMemo(
    () => buildChartData(data, lang),
    [data, lang],
  );

  const tabs = Object.values(SERIES);

  return (
    <section className={`px-4 py-12 sm:px-6 ${className || ''}`}>
      <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {lang === 'fa' ? 'نمودارهای زمان‌سری' : 'Time-series charts'}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {lang === 'fa'
              ? 'نمونه‌های تصویری زیر نمادین هستند؛ داده‌های زنده پس از وصل شدن به سرویس ماهواره‌ای و پایلوت منتشر می‌شود.'
              : 'The charts below are illustrative samples; real data goes live once the satellite service and pilot are connected.'}
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
              }`}
            >
              {lang === 'fa' ? tab.labelFa : tab.labelEn}
            </button>
          ))}
        </div>

        <div className="mx-auto h-72 w-full max-w-[640px]">
          <ResponsiveContainerRaw width="100%" height="100%">
            <AreaChartRaw data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id={`grad-${cfg.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={cfg.color} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={cfg.color} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGridRaw strokeDasharray="3 5" stroke="rgba(255,255,255,0.06)" />
              <XAxisRaw
                dataKey="label"
                tick={{ fill: 'var(--color-night-200)', fontSize: 10 }}
                angle={-30}
                textAnchor="end"
                height={40}
              />
              <YAxisRaw tick={{ fill: 'var(--color-night-200)', fontSize: 10 }} />
              <TooltipRaw
                contentStyle={{
                  background: 'var(--color-night-900)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: 'var(--color-night-100)',
                }}
              />
              <LegendRaw />
              <AreaRaw
                type="monotone"
                dataKey={cfg.key}
                stroke={cfg.color}
                strokeWidth={2}
                fill={`url(#grad-${cfg.key})`}
                strokeLinecap="round"
                strokeLinejoin="round"
                name={lang === 'fa' ? cfg.labelFa : cfg.labelEn}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
            </AreaChartRaw>
          </ResponsiveContainerRaw>
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
