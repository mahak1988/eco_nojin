import { useEffect, useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';

/** Animated live data ticker. */
export default function LiveDataTicker() {
  const { lang } = useLang();
  const [count, setCount] = useState(0);
  const target = 12458;

  useEffect(() => {
    let start = 0;
    const step = Math.ceil(target / 60);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        start = target;
        clearInterval(timer);
      }
      setCount(start);
    }, 30);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center gap-3">
      <span className="live-dot" aria-hidden />
      <span className="text-2xl font-extrabold text-[var(--color-leaf-300)]">{count.toLocaleString()}</span>
      <span className="text-xs text-[var(--color-night-200)]/60">
        {lang === 'fa' ? 'پروژه فعال' : 'Active Projects'}
      </span>
    </div>
  );
}
