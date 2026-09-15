import { useState, useRef, useEffect } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Search, X, ArrowRight } from 'lucide-react';

/** Search with autocomplete suggestions. */
export default function AutocompleteSearch({
  suggestions,
}: {
  suggestions?: string[];
}) {
  const { lang } = useLang();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const defaultSuggestions = [
    'پروژه جنگلشکاری', 'بازسازی تالاب', 'گزارش NDVI', 'مدل سه‌بعدی',
    'آمار بازیابی', 'تغییرات اقلیمی', 'پایش ماهواره‌ای', 'مقایسه پروژه‌ها',
  ];
  const items = suggestions || defaultSuggestions;
  const filtered = query ? items.filter((s) => s.includes(query)) : items;

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="relative" ref={inputRef}>
      <div className="relative">
        <Search className="absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]/40" aria-hidden />
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          placeholder={lang === 'fa' ? 'جستجوی سراسری...' : 'Search...'}
          className="w-full rounded-full bg-white/5 border border-white/10 pl-11 pr-10 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)] focus:outline-none"
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(''); inputRef.current?.focus(); }}
            className="absolute end-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        )}
      </div>
      {open && query && filtered.length > 0 && (
        <div className="absolute top-full mt-2 left-0 right-0 rounded-2xl glass border border-white/10 overflow-hidden z-50">
          {filtered.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => { setQuery(item); setOpen(false); }}
              className="flex items-center gap-2 w-full px-4 py-3 text-sm text-[var(--color-night-100)] hover:bg-white/5 text-left"
            >
              <ArrowRight className="h-3 w-3 text-[var(--color-leaf-400)]" aria-hidden />
              {item}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
