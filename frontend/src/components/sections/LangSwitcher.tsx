import { useLang } from '../../i18n/LanguageContext';
import { ChevronDown, Check } from 'lucide-react';
import { useState } from 'react';

/** Language switcher dropdown for hero or navbar. */
export default function LangSwitcher() {
  const { lang, setLang } = useLang();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-[var(--color-night-100)]"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        {lang === 'fa' ? '🇮🇷 فارسی' : '🇺🇸 English'}
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div
            className="absolute right-0 top-full z-40 mt-2 w-40 overflow-hidden rounded-2xl glass border border-white/10"
            role="listbox"
          >
            <button
              type="button"
              onClick={() => { setLang('fa'); setOpen(false); }}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-bold text-[var(--color-night-100)] hover:bg-white/5"
              role="option"
              aria-selected={lang === 'fa'}
            >
              🇮🇷 فارسی
              {lang === 'fa' && <Check className="ml-auto h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />}
            </button>
            <button
              type="button"
              onClick={() => { setLang('en'); setOpen(false); }}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-bold text-[var(--color-night-100)] hover:bg-white/5"
              role="option"
              aria-selected={lang === 'en'}
            >
              🇺🇸 English
              {lang === 'en' && <Check className="ml-auto h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
