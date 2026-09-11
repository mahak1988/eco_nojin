/** Interactive SVG charts for the dashboard — responsive, animated, with tooltips. */

import { useMemo, useState, useEffect } from 'react';
import { registry, categories } from '../../lib/hydromaregistry';

/* ---------- helpers ---------- */

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const angleRad = (angleDeg - 90) * (Math.PI / 180);
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
}

/* ---------- Pie Chart ---------- */

const PIE_COLORS = [
  'var(--color-leaf-300)',
  'var(--color-aqua-400)',
  'var(--color-sand-400)',
  'var(--color-sand-300)',
  'var(--color-aqua-200)',
  'var(--color-leaf-500)',
  'var(--color-sand-500)',
  'var(--color-aqua-300)',
];

export function CategoryPieChart({ isFa }: { isFa: boolean }) {
  const data = useMemo(() => {
    return categories
      .map((cat, i) => ({
        key: cat.key,
        name: cat.nameEn,
        count: registry.filter((e) => e.category === cat.key).length,
        color: PIE_COLORS[i % PIE_COLORS.length],
      }))
      .filter((d) => d.count > 0);
  }, []);

  const total = data.reduce((sum, d) => sum + d.count, 0);
  const [hovered, setHovered] = useState<number | null>(null);

  let cumulative = 0;
  const slices = data.map((d, i) => {
    const angle = (d.count / total) * 360;
    const startAngle = cumulative;
    cumulative += angle;
    const endAngle = cumulative;
    return { ...d, startAngle, endAngle, index: i };
  });

  return (
    <div className="glass rounded-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
<h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{isFa ? 'توزیع دسته‌ها' : 'Category distribution'}</h3>
<span className="text-[10px] text-[var(--color-night-200)]/40">{isFa ? 'نمودار دایره‌ای' : 'Pie chart'}</span>
      </div>
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <svg viewBox="0 0 200 200" className="h-56 w-56 sm:h-64 sm:w-64">
            <defs>
              <filter id="pieShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.3" />
              </filter>
            </defs>
            <g filter="url(#pieShadow)">
              {slices.map((slice) => {
                const isHovered = hovered === slice.index;
                const midAngle = (slice.startAngle + slice.endAngle) / 2;
                const offset = isHovered ? 6 : 0;
                const midRad = ((midAngle - 90) * Math.PI) / 180;
                const ox = offset * Math.cos(midRad);
                const oy = offset * Math.sin(midRad);
                return (
                  <path
                    key={slice.key}
                    d={describeArc(100, 100, 80, slice.startAngle, slice.endAngle)}
                    fill={slice.color}
                    opacity={isHovered ? 1 : 0.85}
                    stroke="#04100b"
                    strokeWidth="1"
                    transform={`translate(${ox}, ${oy})`}
                    onMouseEnter={() => setHovered(slice.index)}
                    onMouseLeave={() => setHovered(null)}
                    className="transition-all duration-200"
                    style={{ cursor: 'pointer' }}
                  />
                );
              })}
            </g>
            {/* center circle for donut effect */}
            <circle cx="100" cy="100" r="50" fill="#0b241a" />
            <text x="100" y="96" textAnchor="middle" className="fill-[var(--color-night-100)]" style={{ fontSize: '24px', fontWeight: 800 }}>
              {total}
            </text>
            <text x="100" y="116" textAnchor="middle" className="fill-[var(--color-night-200)]" style={{ fontSize: '10px' }}>
              {isFa ? 'مدل' : 'models'}
            </text>
          </svg>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
          {slices.map((slice, i) => (
            <div
              key={slice.key}
              className={`flex items-center gap-2 rounded-xl px-2 py-1.5 transition-colors ${
                hovered === i ? 'bg-[var(--color-night-800)]' : ''
              }`}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: slice.color }} />
            <span className="flex-1 text-[10px] text-[var(--color-night-200)]/65">{slice.name}</span>
            <span className="text-[10px] font-extrabold text-[var(--color-night-100)]" dir="ltr">{slice.count}</span>
            </div>
          ))}
        </div>
        {hovered !== null && (
          <div className="mt-2 rounded-xl bg-[var(--color-night-900)] px-4 py-2 text-center">
          <p className="text-xs font-extrabold text-[var(--color-night-100)]">
            {slices[hovered]?.name} — {slices[hovered]?.count} {isFa ? 'مدل' : 'models'}
          </p>
          <p className="text-[10px] text-[var(--color-night-200)]/55">
            {isFa ? 'درصد' : 'Percentage'}: {((slices[hovered]?.count / total) * 100).toFixed(1)}%
          </p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Bar Chart ---------- */

export function ModelTypeBarChart({ isFa }: { isFa: boolean }) {
  const data = useMemo(() => {
    const calculators = registry.filter((e) => e.impl === 'calculator' || e.impl === 'engine+calculator').length;
    const engine = registry.filter((e) => e.impl === 'engine' || e.impl === 'engine+api').length;
    return [
      { label: isFa ? 'محاسبه‌گر' : 'Calculators', value: calculators, color: '#45bcd4', icon: '🧮' },
      { label: isFa ? 'موتور محاسباتی' : 'Engine', value: engine, color: '#e6b96b', icon: '⚙️' },
    ];
  }, [isFa]);

  const max = Math.max(...data.map((d) => d.value));
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <div className="glass rounded-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{isFa ? 'انواع مدل‌ها' : 'Model types'}</h3>
        <span className="text-[10px] text-[var(--color-night-200)]/40">{isFa ? 'نمودار میله‌ای' : 'Bar chart'}</span>
      </div>
      <div className="flex flex-col gap-4">
        {data.map((d, i) => (
          <div key={i} className="relative">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-lg">{d.icon}</span>
                <span className="text-xs font-bold text-[var(--color-night-200)]/70">{d.label}</span>
              </div>
              <span className="text-sm font-extrabold text-[var(--color-night-100)]" dir="ltr">{d.value}</span>
            </div>
            <div className="relative h-3 w-full overflow-hidden rounded-full bg-[var(--color-night-900)]/60">
              <div
                className="absolute inset-y-0 start-0 rounded-full transition-all duration-500"
                style={{
                  width: `${(d.value / max) * 100}%`,
                  backgroundColor: d.color,
                  boxShadow: hovered === i ? `0 0 20px ${d.color}40` : 'none',
                }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              />
            </div>
            {hovered === i && (
              <div className="mt-2 rounded-xl bg-[var(--color-night-900)]/80 px-3 py-1.5 text-center">
                <p className="text-[10px] text-[var(--color-night-200)]/55">
                  {isFa ? 'درصد' : 'Percentage'}: {((d.value / registry.length) * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
        <div className="mt-4 flex items-center justify-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-[var(--color-aqua-400)]" />
            <span className="text-[10px] text-[var(--color-night-200)]/60">{isFa ? 'محاسبه‌گر' : 'Calculator'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-[var(--color-sand-400)]" />
            <span className="text-[10px] text-[var(--color-night-200)]/60">{isFa ? 'موتور' : 'Engine'}</span>
          </div>
        </div>
    </div>
  );
}

/* ---------- Mini Sparkline ---------- */

export function MiniSparkline({ data, color, width = 120, height = 40 }: { data: number[]; color: string; width?: number; height?: number }) {
  const max = Math.max(...data, 1);
  const points = data
    .map((v, i) => `${(i / Math.max(data.length - 1, 1)) * width},${height - (v / max) * (height - 4) - 2}`)
    .join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-8 w-28 overflow-visible">
      <defs>
        <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        points={points}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ---------- Activity Ring (3D-like) ---------- */

export function ActivityRing({ progress = 0.75, size = 120 }: { progress?: number; size?: number }) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedProgress(progress), 100);
    return () => clearTimeout(timer);
  }, [progress]);

  const currentOffset = circumference * (1 - animatedProgress);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform transition-transform duration-500 hover:scale-105">
        <defs>
          <filter id="ringShadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.4" />
          </filter>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-night-700)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#ringGradient)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={currentOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="transition-all duration-1000 ease-out"
          filter="url(#ringShadow)"
        />
        <defs>
          <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--color-leaf-300)" />
            <stop offset="100%" stopColor="var(--color-aqua-400)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-extrabold text-[var(--color-night-100)]" dir="ltr">{Math.round(animatedProgress * 100)}%</span>
      </div>
    </div>
  );
}
