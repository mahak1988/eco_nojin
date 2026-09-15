import { useMemo } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import EmptyBox from '../ui/EmptyBox';

export interface DataPoint {
  label: string;
  value: number;
  secondary?: number;
}

interface EcoChartProps {
  data: DataPoint[];
  title?: string;
  color?: string;
  height?: number;
}

export function EcoChart({ data, title, color = '#2fb36b', height = 300 }: EcoChartProps) {
  const { lang } = useLang();

  const { width, height: svgHeight, points, areaD, secondaryPoints, yTicks } = useMemo(() => {
    const w = 800;
    const h = height;
    const padding = { top: 20, right: 30, bottom: 40, left: 50 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    const allValues = data.flatMap((d) => [d.value, d.secondary ?? 0]);
    const maxVal = Math.max(...allValues, 1);
    const minVal = 0;

    const yS = (v: number) => padding.top + chartH - ((v - minVal) / (maxVal - minVal)) * chartH;
    const xS = (i: number) => padding.left + (i / Math.max(data.length - 1, 1)) * chartW;

    const yTicksArr = Array.from({ length: 5 }, (_, i) => {
      const val = minVal + ((maxVal - minVal) * i) / 4;
      return { value: val, y: yS(val) };
    });

    const pathD = data
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xS(i)} ${yS(d.value)}`)
      .join(' ');

    const areaD = pathD + ` L ${xS(data.length - 1)} ${padding.top + chartH} L ${xS(0)} ${padding.top + chartH} Z`;

    const secPathD = data.length > 1 && data.some((d) => d.secondary !== undefined)
      ? data
          .filter((d) => d.secondary !== undefined)
          .map((d, i) => {
            const origIdx = data.indexOf(d);
            return `${i === 0 ? 'M' : 'L'} ${xS(origIdx)} ${yS(d.secondary!)}`;
          })
          .join(' ')
      : '';

    return {
      width: w,
      height: h,
      points: pathD,
      areaD,
      secondaryPoints: secPathD,
      yScale: yS,
      yTicks: yTicksArr,
    };
  }, [data, height]);

  if (data.length === 0) {
    return (
      <EmptyBox
        icon="chart"
        title={lang === 'fa' ? 'بدهی داده' : 'No data'}
        description={lang === 'fa'
          ? 'داده‌های نمودار هنوز در دسترس نیست. پس از اتصال به سرویس ماهواره‌ای، نمودارها نمایش داده می‌شوند.'
          : 'Chart data is not yet available. Charts will display once connected to the satellite service.'
        }
      />
    );
  }

  return (
    <div className="w-full">
      {title && (
        <h3 className="mb-4 text-sm font-extrabold text-[var(--color-night-100)]">
          {title}
        </h3>
      )}
      <svg
        viewBox={`0 0 ${width} ${svgHeight}`}
        className="w-full"
        style={{ height }}
        role="img"
        aria-label={title ?? 'Chart'}
      >
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line
              x1={50}
              y1={tick.y}
              x2={width - 30}
              y2={tick.y}
              stroke="rgba(255,255,255,0.08)"
              strokeDasharray="4 4"
            />
            <text
              x={45}
              y={tick.y + 4}
              textAnchor="end"
              fill="var(--color-night-200)"
              fontSize={10}
            >
              {tick.value.toFixed(1)}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <path d={areaD} fill="url(#chartGradient)" />

        {/* Main line */}
        <path d={points} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

        {/* Secondary line */}
        {secondaryPoints && (
          <path d={secondaryPoints} fill="none" stroke="#45bcd4" strokeWidth={2} strokeDasharray="6 4" strokeLinecap="round" />
        )}

        {/* Data points */}
        {data.map((d, i) => {
          const x = 50 + (i / Math.max(data.length - 1, 1)) * (width - 80);
          const y = height - 40 - ((d.value / Math.max(...data.map((dd) => dd.value), 1)) * (height - 60));
          return (
            <circle key={d.label} cx={x} cy={y} r={4} fill={color} />
          );
        })}

        {/* X-axis labels */}
        {data.map((d, i) => {
          const x = 50 + (i / Math.max(data.length - 1, 1)) * (width - 80);
          return (
            <text
              key={d.label}
              x={x}
              y={height - 10}
              textAnchor="middle"
              fill="var(--color-night-200)"
              fontSize={10}
            >
              {d.label.length > 8 ? `${d.label.slice(0, 8)}...` : d.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
