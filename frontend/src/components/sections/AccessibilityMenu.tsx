import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { X, MousePointer } from 'lucide-react';
import { cn } from '../../lib/utils';

/** Accessibility options panel. */
export default function AccessibilityMenu() {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);
  const [fontSize, setFontSize] = useState(16);
  const [highContrast, setHighContrast] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-xl glass p-2 text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]"
        aria-label={lang === 'fa' ? 'دسترسی' : 'Accessibility'}
      >
        <MousePointer className="h-5 w-5" aria-hidden />
      </button>
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-72">
          <div className="rounded-3xl glass p-5 space-y-4 border border-white/10">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'دسترسی' : 'Accessibility'}
              </h3>
              <button type="button" onClick={() => setOpen(false)}>
                <X className="h-4 w-4 text-[var(--color-night-200)]/40" aria-hidden />
              </button>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--color-night-200)]/60">
                  {lang === 'fa' ? 'اندازه فونت' : 'Font Size'}
                </span>
                <div className="flex gap-1">
                  <button type="button" onClick={() => setFontSize((s) => Math.max(12, s - 2))} className="glass px-2 py-1 rounded-lg text-xs">A-</button>
                  <span className="glass px-2 py-1 rounded-lg text-xs font-bold text-[var(--color-leaf-300)]">{fontSize}</span>
                  <button type="button" onClick={() => setFontSize((s) => Math.min(24, s + 2))} className="glass px-2 py-1 rounded-lg text-xs">A+</button>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--color-night-200)]/60">
                  {lang === 'fa' ? 'کنتراست بالا' : 'High Contrast'}
                </span>
                <button
                  type="button"
                  onClick={() => setHighContrast(!highContrast)}
                  className={cn('w-10 h-5 rounded-full transition-all', highContrast ? 'bg-[var(--color-leaf-500)]' : 'bg-white/10')}
                >
                  <span className={cn('block w-4 h-4 rounded-full mt-0.5 transition-all', highContrast ? 'translate-x-5 bg-white' : 'translate-x-0.5 bg-white/30')} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
