import { useState } from 'react';
import { Sparkles, Search } from 'lucide-react';

/** AI-style smart search suggestions. */
export default function SmartSearch({
  onSelect,
}: {
  onSelect?: (query: string) => void;
}) {
  const [query, setQuery] = useState('');
  const [thinking, setThinking] = useState(false);

  const handleSearch = () => {
    setThinking(true);
    setTimeout(() => {
      setThinking(false);
      onSelect?.(query);
    }, 500);
  };

  return (
    <div className="rounded-2xl glass p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />
        <h3 className="text-sm font-bold text-[var(--color-night-100)]">AI Search</h3>
      </div>
      <div className="relative">
        <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]/40" aria-hidden />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="پرسش هوشمند..."
          className="w-full rounded-xl bg-white/5 border border-white/10 pl-10 pr-4 py-2.5 text-sm text-[var(--color-night-100)] focus:outline-none focus:border-[var(--color-leaf-500)]"
        />
      </div>
      {query && thinking && (
        <p className="text-xs text-[var(--color-leaf-300)] animate-pulse">
          در حال تحلیل داده‌ها...
        </p>
      )}
      {!query && (
        <div className="space-y-2">
          {['پیشنهاد: بررسی پروژه‌های فعال جنگلی', 'پیشنهاد: مقایسه بازدهی مناطق مختلف', 'پیشنهاد: تقاضای آینده تأثیر تغییرات اقلیمی'].map((s, i: number) => (
            <button
              key={i}
              type="button"
              onClick={() => { setQuery(s); handleSearch(); }}
              className="w-full text-right text-xs text-[var(--color-night-200)]/60 hover:text-[var(--color-leaf-300)] rounded-lg p-2 hover:bg-white/5 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
