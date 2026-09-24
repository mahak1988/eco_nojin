'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from '@/i18n/navigation';
import { type AppLocale, locales } from '@/i18n/routing';

const NATIVE: Record<AppLocale, string> = {
  fa: 'فارسی',
  en: 'English',
  ar: 'العربية',
  ur: 'اردو',
  de: 'Deutsch',
  es: 'Español',
  fr: 'Français',
  hi: 'हिन्दी',
  it: 'Italiano',
  ms: 'Bahasa Melayu',
  pt: 'Português',
  ru: 'Русский',
  zh: '中文',
  bn: 'বাংলা',
};

/** Language waves from the master plan: wave 0 is fully shipped. */
const WAVE: Partial<Record<AppLocale, string>> = {
  ar: '۰',
  ur: '۰',
  de: '۱',
  es: '۱',
  fr: '۱',
  hi: '۱',
  pt: '۱',
  zh: '۱',
  ru: '۲',
  ms: '۲',
  it: '۲',
  bn: '۲',
};

export function LanguageMenu({
  current,
  label,
  rows = 'auto',
}: {
  current: string;
  label: string;
  rows?: 'auto' | 'compact';
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const active = current as AppLocale;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-sm text-[var(--ink)] transition-colors hover:border-[var(--forest)] hover:bg-[var(--surface-2)]"
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-4 w-4 text-[var(--ink-soft)]"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18M12 3c2.7 3 2.7 15 0 18M12 3c-2.7 3-2.7 15 0 18" />
        </svg>
        <span className="max-w-[8rem] truncate" dir={active === 'fa' || active === 'ar' || active === 'ur' ? 'rtl' : 'ltr'}>
          {NATIVE[active] ?? current}
        </span>
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-3.5 w-3.5 text-[var(--ink-faint)] transition-transform duration-200"
          style={{ transform: open ? 'rotate(180deg)' : 'none' }}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <div
        role="listbox"
        aria-label={label}
        hidden={!open}
        className="absolute end-0 z-50 mt-2 w-64 overflow-hidden rounded-[var(--radius-l)] border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow-pop)]"
      >
        <div className="flex items-center justify-between border-b border-[var(--line)] px-3 py-2">
          <span className="text-[11px] font-semibold text-[var(--ink-soft)]">{label}</span>
          <span className="num text-[10px] text-[var(--ink-faint)]">{locales.length}</span>
        </div>
        <ul className={`p-1 ${rows === 'compact' ? 'max-h-64' : 'max-h-80'} overflow-y-auto`}>
          {locales.map((locale) => {
            const selected = locale === current;
            return (
              <li key={locale}>
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  lang={locale}
                  onClick={() => {
                    setOpen(false);
                    if (!selected) router.replace(pathname, { locale });
                  }}
                  className={[
                    'flex w-full items-center justify-between gap-3 rounded-[var(--radius-m)] px-3 py-2 text-sm transition-colors',
                    selected
                      ? 'bg-[var(--surface-2)] font-semibold text-[var(--ink)]'
                      : 'text-[var(--ink-soft)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]',
                  ].join(' ')}
                >
                  <span className="flex items-center gap-2">
                    {selected ? (
                      <span
                        aria-hidden="true"
                        className="h-1.5 w-1.5 rounded-full bg-[var(--forest)]"
                      />
                    ) : (
                      <span aria-hidden="true" className="h-1.5 w-1.5" />
                    )}
                    <span
                      dir={locale === 'fa' || locale === 'ar' || locale === 'ur' ? 'rtl' : 'ltr'}
                    >
                      {NATIVE[locale as AppLocale]}
                    </span>
                  </span>
                  <span className="num text-[10px] text-[var(--ink-faint)]">
                    {locale.toUpperCase()}
                    {WAVE[locale as AppLocale] ? ` · موج ${WAVE[locale as AppLocale]}` : ''}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
