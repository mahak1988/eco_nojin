import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import { Satellite, Users, Leaf, BarChart3 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const iconMap: Record<string, LucideIcon> = {
  satellite: Satellite,
  people: Users,
  co2: BarChart3,
  leaf: Leaf,
};

interface CounterItem {
  label: string;
  metricKey: string;
  unit: string;
  icon: string;
}

interface LiveCounterProps {
  item: CounterItem;
  delay?: number;
}

function useApiValue(metricKey: string): { value: number | null; error: boolean } {
  const [value, setValue] = useState<number | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchValue = async () => {
      try {
        const resp = await fetch(`/api/v1/impact/${metricKey}`);
        if (!resp.ok) throw new Error(`API error: ${resp.status}`);
        const data = await resp.json();
        setValue(data.value ?? data);
      } catch {
        setError(true);
      }
    };

    fetchValue();
    const interval = setInterval(fetchValue, 30000);
    return () => clearInterval(interval);
  }, [metricKey]);

  return { value, error };
}

/** Single animated counter — falls back to "—" when data is not yet available. */
function LiveCounter({ item, delay = 0 }: LiveCounterProps) {
  const { value, error } = useApiValue(item.metricKey);
  const reduce = useReducedMotion();

  const displayValue = value ?? 0;
  const isAvailable = value !== null && !error;

  const formatNumber = (n: number): string => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(n >= 10000000 ? 0 : 1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K`;
    return n.toLocaleString('fa-IR');
  };

  const IconComponent = iconMap[item.icon] ?? BarChart3;

  return (
    <motion.div
      className="glass glass-hover relative flex flex-col items-center gap-3 rounded-3xl px-5 py-6"
      initial={reduce ? undefined : { opacity: 0, y: 18 }}
      animate={reduce ? undefined : { opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.55, ease: [0.22, 0.61, 0.36, 1] }}
    >
      <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]">
        <IconComponent className="h-5 w-5" aria-hidden />
      </span>

      <motion.span
        className="text-3xl font-extrabold text-[var(--color-night-100)] tabular-nums"
        initial={reduce ? undefined : { opacity: 0 }}
        animate={reduce ? undefined : { opacity: 1 }}
        transition={{ delay: delay + 0.2, duration: 0.4 }}
      >
        {isAvailable ? formatNumber(displayValue) : '—'}
      </motion.span>

      <span className="text-center text-xs font-bold text-[var(--color-night-200)]/60">
        {item.label}
      </span>

      {isAvailable ? null : (
        <span className="absolute top-2 end-2 rounded-full bg-[var(--color-sand-500)]/20 px-1.5 py-0.5 text-[9px] font-bold text-[var(--color-sand-300)]">
          {'coming Soon'}
        </span>
      )}
    </motion.div>
  );
}

/** Live counters bar — attempts to fetch real data from the API, falls back to conceptual display. */
export default function LiveCounters() {
  const { t, lang } = useLang();
  const counters = t.impact.liveCounters;

  return (
    <section className="px-4 py-14 sm:px-6" id="live-stats">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {counters.title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {counters.note}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {counters.items.map((item, index) => (
            <LiveCounter key={item.metricKey} item={item} delay={index * 0.08} />
          ))}
        </div>

        <p className="text-center text-[10px] text-[var(--color-night-200)]/35">
          {lang === 'fa'
            ? 'داده‌های بالا از سرویس API دریافت می‌شوند؛ پس از آغاز پایلوت زنده می‌شوند.'
            : 'The data above is fetched from the API; it goes live with the pilot.'}
        </p>
      </div>

      <style>{`
        @media (prefers-reduced-motion: reduce) {
          .motion\\:animate-none { animation: none; }
        }
      `}</style>
    </section>
  );
}
