/** Animated rain + lightning background panel — used on the registration
 * card to give the page a living, atmospheric backdrop. Pure CSS/SVG,
 * zero dependencies, respects prefers-reduced-motion. */

import { useEffect, useState } from 'react';
import type { Lang } from '../../content/site';

interface RainBackgroundProps {
  lang?: Lang;
}

const COPY = {
  fa: {
    brand: 'ECO NOJIN',
    title: 'اکونوژین را بساز،\nزیست را بکار.',
    desc: '۱۲ بستهٔ فنی-مهندسی، ۶۱ مدل علمی و یک پایلوت زنده برای احیای خاک، آب و کربن. ثبت‌نام رایگان است و هیچ دادهٔ شخصی ذخیره نمی‌شود.',
    tags: ['رایگان', 'بدون IP', 'بدون داده شخصی'],
  },
  en: {
    brand: 'ECO NOJIN',
    title: 'Build Eco Nojin,\nrestore life.',
    desc: '12 engineering packages, 61 scientific models, and one live pilot for soil, water, and carbon restoration. Registration is free — no IP, no personal data stored.',
    tags: ['Free', 'No IP', 'No personal data'],
  },
};

export default function RainBackground({ lang = 'fa' }: RainBackgroundProps) {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const listener = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', listener);
    return () => mq.removeEventListener('change', listener);
  }, []);

  // Build a deterministic rain pattern so SSR and client match.
  const drops = Array.from({ length: 48 }, (_, i) => ({
    id: i,
    x: (i * 37) % 100,
    delay: (i * 0.07) % 1.4,
    duration: 0.6 + ((i * 0.13) % 0.8),
    height: 12 + ((i * 7) % 18),
  }));

  return (
    <div className="relative overflow-hidden rounded-3xl">
      {/* night sky gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a1810] via-[#0d2818] to-[#06120a]" />

      {/* distant glow */}
      <div className="absolute -top-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-[var(--color-leaf-500)]/20 blur-3xl" />

      {/* rain layer */}
      <div
        className="absolute inset-0 opacity-70"
        aria-hidden
        style={
          reduced
            ? undefined
            : {
                background:
                  'linear-gradient(to bottom, transparent 0%, rgba(180,220,200,0.05) 45%, rgba(180,220,200,0.18) 50%, transparent 55%, transparent 100%)',
                backgroundSize: '100% 120px',
                animation: 'rainFall 0.7s linear infinite',
              }
        }
      >
        <svg className="h-full w-full" xmlns="http://www.w3.org/2000/svg">
          {drops.map((d) => (
            <line
              key={d.id}
              x1={`${d.x}%`}
              y1="0"
              x2={`${d.x - 1}%`}
              y2={`${d.height}%`}
              stroke="rgba(200,230,220,0.35)"
              strokeWidth="1.5"
              style={
                reduced
                  ? undefined
                  : {
                      animation: `rainDrop ${d.duration}s linear ${d.delay}s infinite`,
                      transformOrigin: 'top center',
                    }
              }
            />
          ))}
        </svg>
      </div>

      {/* lightning flash layer */}
      {!reduced && (
        <div
          className="absolute inset-0 opacity-0"
          style={{
            animation: 'lightning 6s ease-in-out infinite',
            background:
              'linear-gradient(135deg, rgba(255,255,255,0.0) 0%, rgba(220,240,255,0.18) 45%, rgba(255,255,255,0.0) 50%, rgba(220,240,255,0.10) 55%, transparent 100%)',
          }}
          aria-hidden
        />
      )}

      {/* ground reflection */}
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/40 to-transparent" />

      {/* content */}
      <div className="relative z-10 flex h-full flex-col justify-end p-8">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-[var(--color-leaf-300)]" />
          <span className="text-[10px] font-extrabold tracking-[0.25em] text-[var(--color-leaf-300)]/80">
            {COPY[lang as 'fa' | 'en'].brand}
          </span>
        </div>
        <h2 className="mt-3 text-2xl font-extrabold leading-snug text-white">
          {COPY[lang as 'fa' | 'en'].title}
        </h2>
        <p className="mt-3 text-xs leading-6 text-white/70">
          {COPY[lang as 'fa' | 'en'].desc}
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          {COPY[lang as 'fa' | 'en'].tags.map((tag: string) => (
            <span
              key={tag}
              className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[10px] font-bold text-white/70"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes rainFall {
          from { background-position: 0 0; }
          to { background-position: 0 120px; }
        }
        @keyframes rainDrop {
          from { transform: translateY(-20px); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          to { transform: translateY(0); opacity: 0; }
        }
        @keyframes lightning {
          0%, 92%, 100% { opacity: 0; }
          93% { opacity: 0.5; }
          94% { opacity: 0.15; }
          95% { opacity: 0.7; }
          96% { opacity: 0.2; }
          97% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}