import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import { Satellite, Users, Leaf, BarChart3, Wifi, WifiOff } from 'lucide-react';
import { useLiveMetrics, ConnectionStatusIndicator } from '../../hooks/useRealtimeData';
import type { LucideIcon } from 'lucide-react';
import type { Lang } from '../../content/site';

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
  value: number;
  isLive: boolean;
  delay?: number;
}

function formatNumber(n: number, lang: Lang): string {
  const locale = lang === 'fa' ? 'fa-IR' : 'en-US';
  if (n >= 1000000) return `${(n / 1000000).toFixed(n >= 10000000 ? 0 : 1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K`;
  return n.toLocaleString(locale);
}

function LiveCounter({ item, value, isLive, delay = 0 }: LiveCounterProps) {
  const { lang } = useLang();
  const reduce = useReducedMotion();

  const IconComponent = iconMap[item.icon] ?? BarChart3;

  // ARIA live region for announcing value changes
  const liveRegionId = `live-counter-${item.metricKey}`;

  return (
    <motion.div
      className="glass glass-hover relative flex flex-col items-center gap-3 rounded-3xl px-5 py-6"
      initial={reduce ? undefined : { opacity: 0, y: 18 }}
      animate={reduce ? undefined : { opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.55, ease: [0.22, 0.61, 0.36, 1] }}
    >
      <div className="relative">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]">
          <IconComponent className="h-5 w-5" aria-hidden />
        </span>
        {isLive && (
          <span
            className="absolute -top-1 -end-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-leaf-500)]"
            aria-hidden
          >
            <Wifi className="h-2.5 w-2.5 text-[var(--color-night-950)]" aria-hidden />
          </span>
        )}
        {!isLive && (
          <span
            className="absolute -top-1 -end-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-gray-500/30"
            aria-hidden
          >
            <WifiOff className="h-2.5 w-2.5 text-gray-400" aria-hidden />
          </span>
        )}
      </div>

      <div className="relative" aria-live="polite" aria-atomic="true" id={liveRegionId}>
        <motion.span
          className="text-3xl font-extrabold text-[var(--color-night-100)] tabular-nums"
          initial={reduce ? undefined : { opacity: 0 }}
          animate={reduce ? undefined : { opacity: 1 }}
          transition={{ delay: delay + 0.2, duration: 0.4 }}
        >
          {isLive ? formatNumber(value, lang) : '—'}
        </motion.span>
      </div>

      <span className="text-center text-xs font-bold text-[var(--color-night-200)]/60">
        {item.label}
      </span>

      {!isLive && (
        <span className="absolute top-2 end-2 rounded-full bg-[var(--color-sand-500)]/20 px-1.5 py-0.5 text-[9px] font-bold text-[var(--color-sand-300)]">
          {lang === 'fa' ? 'به زودی' : 'Coming Soon'}
        </span>
      )}
    </motion.div>
  );
}

/** Live counters bar — uses real-time WebSocket/SSE data when available. */
export default function LiveCounters() {
  const { t, lang } = useLang();
  const counters = t.impact.liveCounters;
  const { metrics, state, reconnect, isLive } = useLiveMetrics(lang);

  const metricKeyMap: Record<string, keyof typeof metrics> = {
    area_ha: 'area_ha',
    farmers_trained: 'farmers_trained',
    co2_sequestered_tco2e: 'co2_sequestered_tco2e',
    credits_issued: 'credits_issued',
  };

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
          <div className="mt-3 flex items-center gap-3">
            <ConnectionStatusIndicator state={state} />
            {state === 'error' && (
              <button
                type="button"
                onClick={reconnect}
                className="glass glass-hover inline-flex items-center gap-1.5 rounded-full border border-[var(--color-sand-500)]/40 bg-[var(--color-sand-500)]/10 px-3 py-1.5 text-xs font-bold text-[var(--color-sand-300)]"
              >
                <span className="animate-spin">🔄</span>
                {lang === 'fa' ? 'تلاش مجدد' : 'Retry'}
              </button>
            )}
            {state === 'disconnected' && (
              <button
                type="button"
                onClick={reconnect}
                className="glass glass-hover inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-bold text-[var(--color-night-200)]/60"
              >
                🔄
                {lang === 'fa' ? 'اتصال مجدد' : 'Reconnect'}
              </button>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {counters.items.map((item, index) => {
            const metricKey = metricKeyMap[item.metricKey];
            const value = metricKey ? metrics[metricKey] : 0;
            return (
              <LiveCounter
                key={item.metricKey}
                item={item}
                value={value}
                isLive={isLive}
                delay={index * 0.08}
              />
            );
          })}
        </div>

        <p className="text-center text-[10px] text-[var(--color-night-200)]/35">
          {isLive
            ? lang === 'fa'
              ? 'داده‌های زنده از طریق WebSocket/SSE دریافت می‌شوند.'
              : 'Live data received via WebSocket/SSE.'
            : lang === 'fa'
              ? 'اتصال به سرور برقرار نشد. پس از آغاز پایلوت زنده می‌شوند.'
              : 'Server connection failed. Goes live with pilot.'}
        </p>
      </div>
    </section>
  );
}
