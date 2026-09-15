import { useEffect, useRef, useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface CounterStat {
  value: number;
  suffix?: string;
  label: string;
}

/** Animated counter that counts up when scrolled into view. */
function AnimatedCounter({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            const duration = 1500;
            const startTime = performance.now();

            const animate = (now: number) => {
              const elapsed = now - startTime;
              const progress = Math.min(elapsed / duration, 1);
              const eased = 1 - Math.pow(1 - progress, 3);
              setCount(Math.round(eased * target));
              if (progress < 1) requestAnimationFrame(animate);
            };

            requestAnimationFrame(animate);
          }
        });
      },
      { threshold: 0.5 },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [target]);

  return (
    <span ref={ref} dir="ltr">
      {count.toLocaleString()}
      {suffix}
    </span>
  );
}

/** Animated stat counters band. */
export default function LiveCounters() {
  const { lang } = useLang();

  const stats: CounterStat[] = [
    { value: 30, suffix: '+', label: lang === 'fa' ? 'زیرماژول علمی' : 'Scientific Modules' },
    { value: 38, suffix: '', label: lang === 'fa' ? 'سرویس میکروسرویس' : 'Microservices' },
    { value: 5, suffix: '', label: lang === 'fa' ? 'کانال دسترسی' : 'Access Channels' },
    { value: 14, suffix: '', label: lang === 'fa' ? 'زبان' : 'Languages' },
    { value: 25, suffix: 'M', label: lang === 'fa' ? 'کشاورز خرد (میلیون)' : 'Small Farmers (M)' },
    { value: 8, suffix: '', label: lang === 'fa' ? 'شاخص پوشش گیاهی' : 'Vegetation Indices' },
  ];

  return (
    <section className="px-4 py-10 sm:px-6" aria-label="Live statistics">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 0.06}>
            <div className="flex flex-col items-center gap-1 rounded-3xl glass p-4 text-center">
              <div className="text-2xl font-extrabold text-[var(--color-leaf-300)] sm:text-3xl">
                <AnimatedCounter target={stat.value} suffix={stat.suffix} />
              </div>
              <p className="text-xs text-[var(--color-night-200)]/60">{stat.label}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
