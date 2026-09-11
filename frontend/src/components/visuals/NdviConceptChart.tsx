/** Conceptual NDVI time-series sample chart (SVG, animated draw) — clearly
 * labelled as an illustrative sample; live data arrives with the pilot. */

import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';

const POINTS = [0.22, 0.26, 0.34, 0.31, 0.4, 0.48, 0.45, 0.55, 0.62, 0.58, 0.68, 0.74];
const MONTHS_FA = ['فر', 'ار', 'خرد', 'تیر', 'م', 'شهر', 'مه', 'آب', 'آذر', 'دی', 'بهمن', 'اسف'];
const MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Maps an NDVI value (0–1) onto the chart's y coordinate. */
function toY(value: number, height: number, pad: number): number {
  return height - pad - value * (height - pad * 2);
}

export default function NdviConceptChart() {
  const { t, lang } = useLang();
  const reduce = useReducedMotion();

  const width = 560;
  const height = 220;
  const pad = 26;
  const stepX = (width - pad * 2) / (POINTS.length - 1);
  const points = POINTS.map((v, i) => [pad + i * stepX, toY(v, height, pad)] as const);
  const line = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  const area = `${line} L${(pad + (POINTS.length - 1) * stepX).toFixed(1)} ${height - pad} L${pad} ${height - pad} Z`;

  return (
    <figure className="glass rounded-3xl p-6">
      <figcaption className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
          {lang === 'fa' ? 'روند NDVI — نمونهٔ تصویری' : 'NDVI trend — illustrative sample'}
        </h3>
        <span className="rounded-full bg-[var(--color-aqua-500)]/12 px-3 py-1 text-[10px] font-bold text-[var(--color-aqua-300)]">
          {t.common.conceptual}
        </span>
      </figcaption>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={lang === 'fa' ? 'نمودار نمونهٔ NDVI' : 'Sample NDVI chart'}>
        <defs>
          <linearGradient id="ndvi-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2fb36b" stopOpacity="0.45" />
            <stop offset="1" stopColor="#2fb36b" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* grid */}
        {[0.25, 0.5, 0.75].map((f) => (
          <line
            key={f}
            x1={pad}
            x2={width - pad}
            y1={toY(f, height, pad)}
            y2={toY(f, height, pad)}
            stroke="rgba(255,255,255,0.06)"
            strokeDasharray="3 5"
          />
        ))}

        {/* area + line */}
        <motion.path
          d={area}
          fill="url(#ndvi-area)"
          initial={reduce ? undefined : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
        />
        <motion.path
          d={line}
          fill="none"
          stroke="#7ee2a8"
          strokeWidth="2.5"
          strokeLinecap="round"
          initial={reduce ? undefined : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.6, ease: 'easeInOut' }}
        />

        {/* points */}
        {points.map(([x, y], i) => (
          <motion.circle
            key={i}
            cx={x}
            cy={y}
            r="3.5"
            fill="#04100b"
            stroke="#7ee2a8"
            strokeWidth="2"
            initial={reduce ? undefined : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 + i * 0.1 }}
          />
        ))}

        {/* month labels */}
        {(lang === 'fa' ? MONTHS_FA : MONTHS_EN).map((m, i) => (
          <text
            key={m + i}
            x={pad + i * stepX}
            y={height - 6}
            textAnchor="middle"
            fontSize="9"
            fill="rgba(230,242,234,0.4)"
          >
            {m}
          </text>
        ))}
      </svg>

      <p className="mt-3 text-[11px] leading-5 text-[var(--color-night-200)]/40">
        {lang === 'fa'
          ? 'شکل بالا یک نمونهٔ تصویری از خروجی صفحهٔ پایش است؛ دادهٔ واقعی سری‌های زمانی پس از اتصال به سرویس ماهواره و پایلوت، در همین نمودار زنده می‌شود.'
          : 'The chart above is an illustrative sample of the monitoring output; real time-series data goes live here once the satellite service and pilot are connected.'}
      </p>
    </figure>
  );
}
