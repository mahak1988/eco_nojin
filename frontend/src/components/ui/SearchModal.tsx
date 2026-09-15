/** Global Search — Fuse.js client-side search with Cmd+K modal. */

import { useState, useEffect, useCallback, useRef, use } from 'react';
import { X, Search, Command, Keyboard, ArrowUp, ArrowDown } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import { content } from '../../content/site';
import { useFocusTrap } from '../../hooks/useFocusTrap';

const fuseImport = import('fuse.js');

interface SearchResult {
  id: string;
  title: string;
  description: string;
  url: string;
  category: string;
  section: string;
}

const SEARCH_INDEX_KEY = 'econojin-search-index';

function buildSearchIndex(): SearchResult[] {
  const results: SearchResult[] = [];
  
  // Index all pages from content
  Object.entries(content.fa).forEach(([sectionKey, section]) => {
    if (section && typeof section === 'object') {
      Object.entries(section).forEach(([key, value]) => {
        if (typeof value === 'string' && value.length > 10) {
          results.push({
            id: `${sectionKey}.${key}`,
            title: key,
            description: value.slice(0, 200),
            url: `/${sectionKey}`,
            category: sectionKey,
            section: key,
          });
        } else if (Array.isArray(value)) {
          value.forEach((item, index) => {
            if (item && typeof item === 'object') {
              const title = (item as any).title || (item as any).name || `${key}[${index}]`;
              const desc = (item as any).desc || (item as any).description || (item as any).excerpt || '';
              if (typeof title === 'string') {
                results.push({
                  id: `${sectionKey}.${key}.${index}`,
                  title: String(title),
                  description: String(desc).slice(0, 200),
                  url: `/${sectionKey}`,
                  category: sectionKey,
                  section: key,
                });
              }
            }
          });
        }
      });
    }
  });

  return results;
}

function getOrBuildIndex(): SearchResult[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const cached = localStorage.getItem(SEARCH_INDEX_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // ignore
  }
  
  const index = buildSearchIndex();
  try {
    localStorage.setItem(SEARCH_INDEX_KEY, JSON.stringify(index));
  } catch {
    // ignore
  }
  return index;
}

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const { lang } = useLang();
  const reduce = useReducedMotion();
  const Fuse = use(fuseImport).default;
  const fuseInstanceRef = useRef<any>(null);
  if (!fuseInstanceRef.current) {
    const index = getOrBuildIndex();
    fuseInstanceRef.current = new Fuse(index, {
      keys: ['title', 'description', 'category', 'section'],
      threshold: 0.4,
      includeScore: true,
      includeMatches: true,
      minMatchCharLength: 2,
      ignoreLocation: true,
    });
  }
  const fuse = fuseInstanceRef.current;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const modalRef = useFocusTrap(isOpen, onClose);

  const search = useCallback((q: string) => {
    if (!q.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const searchResults = fuse.search(q);
      setResults(searchResults.map((r: any) => r.item).slice(0, 8));
      setSelectedIndex(0);
    } catch (err) {
      console.error('[Search] Error:', err);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [fuse]);

  useEffect(() => {
    const debounce = setTimeout(() => search(query), 150);
    return () => clearTimeout(debounce);
  }, [query, search]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
      
      const handleKeyDown = (e: KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
          e.preventDefault();
          onClose();
        }
        if (e.key === 'Escape') {
          onClose();
        }
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
        }
        if (e.key === 'Enter' && results[selectedIndex]) {
          e.preventDefault();
          window.location.href = results[selectedIndex].url;
          onClose();
        }
      };
      
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, results, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <motion.div
      ref={modalRef}
      className="fixed inset-0 z-[100] flex items-start justify-center pt-16"
      initial={reduce ? undefined : { opacity: 0 }}
      animate={reduce ? undefined : { opacity: 1 }}
      exit={reduce ? undefined : { opacity: 0 }}
      transition={{ duration: 0.15 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={lang === 'fa' ? 'جستجوی سراسری' : 'Global search'}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <motion.div
        className="relative w-full max-w-2xl mx-4 glass rounded-3xl shadow-2xl overflow-hidden"
        initial={reduce ? undefined : { opacity: 0, y: -20, scale: 0.95 }}
        animate={reduce ? undefined : { opacity: 1, y: 0, scale: 1 }}
        exit={reduce ? undefined : { opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="p-4 border-b border-white/10">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-[var(--color-night-200)]/50" aria-hidden />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder={lang === 'fa' ? 'جستجوی سراسری… (⌘K)' : 'Search everywhere… (⌘K)'}
              className="w-full pl-12 pr-12 py-3 rounded-xl bg-[var(--color-night-900)] border border-white/10 text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-400)]/60 focus:outline-none text-base"
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-[var(--color-night-200)]/50 hover:text-[var(--color-night-100)]"
                aria-label={lang === 'fa' ? 'پاک کردن' : 'Clear'}
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
          <div className="mt-2 flex items-center gap-2 text-[11px] text-[var(--color-night-200)]/40">
            <kbd className="inline-flex items-center gap-1 rounded bg-white/5 px-2 py-0.5 font-mono">
              <Command className="h-3 w-3" />
              <span>K</span>
            </kbd>
            <span>{lang === 'fa' ? 'برای باز/بستن' : 'to toggle'}</span>
            {results.length > 0 && (
              <>
                <span>•</span>
                <kbd className="inline-flex items-center gap-1 rounded bg-white/5 px-2 py-0.5 font-mono">
                  <ArrowUp className="h-3 w-3" />
                </kbd>
                <kbd className="inline-flex items-center gap-1 rounded bg-white/5 px-2 py-0.5 font-mono">
                  <ArrowDown className="h-3 w-3" />
                </kbd>
                <span>{lang === 'fa' ? 'ناوبری' : 'navigate'}</span>
                <span>•</span>
                <kbd className="inline-flex items-center gap-1 rounded bg-white/5 px-2 py-0.5 font-mono">Enter</kbd>
                <span>{lang === 'fa' ? 'انتخاب' : 'select'}</span>
              </>
            )}
          </div>
        </div>

        {/* Results */}
        <div
          ref={resultsRef}
          className="max-h-[50vh] overflow-y-auto p-2"
          role="listbox"
          aria-label={lang === 'fa' ? 'نتایج جستجو' : 'Search results'}
        >
          {/* Live region for search results count */}
          <div aria-live="polite" aria-atomic="true" className="sr-only">
            {isLoading
              ? (lang === 'fa' ? 'در حال جستجو…' : 'Searching…')
              : query && results.length === 0
              ? (lang === 'fa' ? 'هیچ نتیجه‌ای یافت نشد' : 'No results found')
              : results.length > 0
              ? (lang === 'fa' ? `${results.length} نتیجه یافت شد` : `${results.length} results found`)
              : ''
            }
          </div>
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/25 border-t-leaf-400" />
              <span className="ml-3 text-sm text-[var(--color-night-200)]/60">
                {lang === 'fa' ? 'در حال جستجو…' : 'Searching…'}
              </span>
            </div>
          )}
          
          {!isLoading && query && results.length === 0 && (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <Search className="h-10 w-10 text-[var(--color-night-200)]/30" />
              <p className="text-sm text-[var(--color-night-200)]/60">
                {lang === 'fa' ? 'نتیجه‌ای یافت نشد' : 'No results found'}
              </p>
              <p className="text-xs text-[var(--color-night-200)]/40">
                {lang === 'fa' ? 'عبارت جستجوی دیگری امتحان کنید' : 'Try a different search term'}
              </p>
            </div>
          )}
          
          {!isLoading && results.length > 0 && (
            <ul className="divide-y divide-white/5" role="list">
              {results.map((result, index) => (
                <li
                  key={result.id}
                  className={`flex items-start gap-3 px-2 py-3 rounded-xl transition-colors cursor-pointer ${
                    index === selectedIndex
                      ? 'bg-[var(--color-leaf-500)]/10'
                      : 'hover:bg-white/5'
                  }`}
                  role="option"
                  aria-selected={index === selectedIndex}
                  onClick={() => {
                    window.location.href = result.url;
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-leaf-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-leaf-300)]">
                        {result.category}
                      </span>
                      <span className="text-[10px] text-[var(--color-night-200)]/40">{result.section}</span>
                    </div>
                    <h4 className="mt-1 font-bold text-[var(--color-night-100)] truncate">{result.title}</h4>
                    <p className="mt-1 text-sm text-[var(--color-night-200)]/60 line-clamp-2">{result.description}</p>
                  </div>
                  <Keyboard className="h-5 w-5 text-[var(--color-night-200)]/30 shrink-0" aria-hidden />
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/10 text-center">
          <p className="text-[10px] text-[var(--color-night-200)]/40">
            {lang === 'fa' ? 'قدرت گرفته از Fuse.js — جستجوی آفلاین' : 'Powered by Fuse.js — offline search'}
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

/** Keyboard shortcut handler — attaches to document for Cmd+K */
export function useGlobalSearchShortcut(onOpen: () => void) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onOpen();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onOpen]);
}