import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';

/**
 * Hero visual: a stylized "satellite view" of agricultural fields tinted by
 * an NDVI-like palette, with an orbiting satellite, a sweeping scan line and
 * floating data-source chips. Decorative and labelled as conceptual.
 */
export default function FieldScene() {
  const { t } = useLang();
  const reduceMotion = useReducedMotion();

  const chips = [
    { label: t.hero.chips.ndvi, cls: 'top-[6%] start-[-4%]', delay: 0 },
    { label: t.hero.chips.era5, cls: 'bottom-[18%] end-[-6%]', delay: 1.1 },
    { label: t.hero.chips.soc, cls: 'bottom-[-4%] start-[10%]', delay: 2 },
  ];

  return (
    <div className="relative mx-auto w-full max-w-[540px]">
      {/* glow */}
      <div
        className="absolute inset-6 rounded-full opacity-40 blur-3xl"
        style={{ background: 'radial-gradient(circle, rgba(47,179,107,0.5) 0%, transparent 70%)' }}
        aria-hidden
      />

      <div className="glass relative aspect-square overflow-hidden rounded-[2rem] shadow-2xl shadow-leaf-900/40">
        <svg viewBox="0 0 400 400" className="absolute inset-0 h-full w-full" aria-hidden>
          <defs>
            <linearGradient id="ndvi-low" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#d49b3f" />
              <stop offset="1" stopColor="#a3a13f" />
            </linearGradient>
            <linearGradient id="ndvi-mid" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#7fb069" />
              <stop offset="1" stopColor="#3f9e5f" />
            </linearGradient>
            <linearGradient id="ndvi-high" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#2fb36b" />
              <stop offset="1" stopColor="#177246" />
            </linearGradient>
          </defs>

          {/* fields — center-pivot circles and strip parcels */}
          <circle cx="108" cy="126" r="72" fill="url(#ndvi-low)" opacity="0.85" />
          <circle cx="108" cy="126" r="72" fill="none" stroke="rgba(255,255,255,0.12)" />
          <circle cx="108" cy="126" r="46" fill="none" stroke="rgba(255,255,255,0.08)" />

          <circle cx="238" cy="92" r="52" fill="url(#ndvi-mid)" opacity="0.9" />
          <circle cx="238" cy="92" r="52" fill="none" stroke="rgba(255,255,255,0.12)" />

          <circle cx="298" cy="238" r="66" fill="url(#ndvi-high)" opacity="0.9" />
          <circle cx="298" cy="238" r="66" fill="none" stroke="rgba(255,255,255,0.12)" />
          <circle cx="298" cy="238" r="40" fill="none" stroke="rgba(255,255,255,0.08)" />

          <rect x="52" y="238" width="58" height="52" rx="8" fill="url(#ndvi-mid)" opacity="0.75" />
          <rect x="116" y="238" width="58" height="52" rx="8" fill="url(#ndvi-low)" opacity="0.75" />
          <rect x="52" y="296" width="58" height="52" rx="8" fill="url(#ndvi-low)" opacity="0.65" />
          <rect x="116" y="296" width="58" height="52" rx="8" fill="url(#ndvi-mid)" opacity="0.8" />
          <rect x="180" y="296" width="58" height="52" rx="8" fill="url(#ndvi-high)" opacity="0.7" />

          <circle cx="330" cy="128" r="34" fill="url(#ndvi-mid)" opacity="0.6" />

          {/* orbit + satellite */}
          <ellipse
            cx="200"
            cy="200"
            rx="185"
            ry="80"
            fill="none"
            stroke="#7ee2a8"
            strokeOpacity="0.35"
            strokeWidth="1.4"
            strokeDasharray="5 7"
            transform="rotate(-18 200 200)"
          />
          <g
            className={reduceMotion ? undefined : 'animate-orbit'}
            style={reduceMotion ? undefined : { transformOrigin: '200px 200px' }}
          >
            <g transform="translate(385 200) rotate(-18)">
              <circle r="5.5" fill="#e6b96b" />
              <rect x="-14" y="-3.4" width="8" height="6.8" rx="1.6" fill="#7fd8e8" />
              <rect x="6" y="-3.4" width="8" height="6.8" rx="1.6" fill="#7fd8e8" />
            </g>
          </g>
        </svg>

        {/* scan line */}
        <div
          className={`absolute inset-x-0 top-1/2 h-24 ${reduceMotion ? '' : 'animate-scan'}`}
          style={{
            background:
              'linear-gradient(180deg, transparent 0%, rgba(126,226,168,0.16) 45%, rgba(126,226,168,0.5) 50%, rgba(126,226,168,0.16) 55%, transparent 100%)',
          }}
          aria-hidden
        />

        {/* frame caption */}
        <span className="absolute bottom-3 start-4 text-[10px] tracking-widest text-[var(--color-night-200)]/40">
          {t.common.conceptual.toUpperCase()}
        </span>
      </div>

      {/* floating chips */}
      {chips.map((chip) => (
        <motion.span
          key={chip.label}
          className={`glass absolute z-10 rounded-full px-3.5 py-1.5 text-xs font-bold text-[var(--color-night-100)] shadow-lg ${chip.cls}`}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={reduceMotion ? { opacity: 1, scale: 1 } : { opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 + chip.delay * 0.4, duration: 0.5 }}
        >
          <span className={reduceMotion ? '' : 'inline-block animate-float'}>{chip.label}</span>
        </motion.span>
      ))}
    </div>
  );
}
