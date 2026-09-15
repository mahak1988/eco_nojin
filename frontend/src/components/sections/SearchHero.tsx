import { useLang } from '../../i18n/LanguageContext';
import { Search } from 'lucide-react';
import { useState } from 'react';

/** Search box integrated in hero area. */
export default function SearchHero() {
  const { lang } = useLang();
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(query.trim())}`;
    }
  };

  return (
    <form onSubmit={handleSearch} className="mt-6 w-full max-w-lg mx-auto">
      <div className="relative">
        <Search className="absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]/40" aria-hidden />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={lang === 'fa' ? 'جستجو در پلتفرم...' : 'Search platform...'}
          className="w-full rounded-full bg-white/5 border border-white/10 pl-11 pr-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)] focus:outline-none"
          aria-label={lang === 'fa' ? 'جستجو' : 'Search'}
        />
        <button
          type="submit"
          className="absolute end-2 top-1/2 -translate-y-1/2 rounded-full bg-[var(--color-leaf-500)] px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-950)] hover:bg-[var(--color-leaf-400)] transition-colors"
        >
          {lang === 'fa' ? 'جستجو' : 'Search'}
        </button>
      </div>
    </form>
  );
}
