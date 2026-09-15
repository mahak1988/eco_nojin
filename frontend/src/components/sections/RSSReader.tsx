import { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';
import { NEWS_DATA } from '../../data/homeData';

/** RSS feed reader with auto-update. */
export default function RSSReader() {
  const [items, setItems] = useState(NEWS_DATA);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setLoading(true);
      const newItem = {
        title: `آپدیت ${new Date().toLocaleTimeString('fa-IR')}`,
        date: new Date().toLocaleDateString('fa-IR'),
        excerpt: 'آخرین بروزرسانی از پلتفرم Eco Nojin.',
        category: 'آپدیت',
      };
      setItems((prev) => [newItem, ...prev.slice(0, 9)]);
      setTimeout(() => setLoading(false), 1000);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-orange-400" aria-hidden>📡</span>
        <span className="text-xs font-bold text-[var(--color-night-100)]">RSS Feed</span>
        {loading && <span className="live-dot" aria-hidden />}
      </div>
      <div className="space-y-2">
        {items.slice(0, 5).map((item, i) => (
          <div key={i} className="flex items-center gap-3 rounded-xl glass p-3 hover:bg-white/[0.06] transition-colors">
            <span className={cn('w-2 h-2 rounded-full shrink-0', i === 0 && loading ? 'bg-[var(--color-leaf-500)] animate-pulse' : 'bg-[var(--color-night-700)]')} aria-hidden />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-[var(--color-night-100)] truncate">{item.title}</p>
              <p className="text-[10px] text-[var(--color-night-200)]/40">{item.date}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
