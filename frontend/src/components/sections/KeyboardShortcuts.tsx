import { useEffect, useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Keyboard, X } from 'lucide-react';

/** Keyboard shortcuts overlay. */
export default function KeyboardShortcuts() {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(!open);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  const shortcuts = [
    { key: 'Ctrl+K', action: lang === 'fa' ? 'جستجو' : 'Search' },
    { key: 'Ctrl+/', action: lang === 'fa' ? 'میانبرها' : 'Shortcuts' },
    { key: 'Esc', action: 'بستن' },
  ];

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-xl glass p-2 text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]"
        aria-label="Shortcuts"
      >
        <Keyboard className="h-5 w-5" aria-hidden />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setOpen(false)}>
      <div className="rounded-3xl glass p-6 w-80 border border-white/10" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-[var(--color-night-100)]">
            {lang === 'fa' ? 'میانبرهای صفحه‌کلید' : 'Keyboard Shortcuts'}
          </h3>
          <button type="button" onClick={() => setOpen(false)}>
            <X className="h-4 w-4 text-[var(--color-night-200)]/40" aria-hidden />
          </button>
        </div>
        <div className="space-y-3">
          {shortcuts.map(({ key, action }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-xs text-[var(--color-night-200)]/60">{action}</span>
              <kbd className="rounded-lg bg-white/5 px-2 py-1 text-xs font-bold text-[var(--color-leaf-300)]">{key}</kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
