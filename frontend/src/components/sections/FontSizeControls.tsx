import { useState } from 'react';
import { cn } from '../../lib/utils';
import { useLang } from '../../i18n/LanguageContext';

/** Font size accessibility controls. */
export default function FontSizeControls() {
  const { lang } = useLang();
  const [size, setSize] = useState(16);

  return (
    <div className="flex items-center gap-3 rounded-2xl glass p-3">
      <span className="text-xs text-[var(--color-night-200)]/60">
        {lang === 'fa' ? 'اندازه فونت' : 'Font Size'}
      </span>
      {[14, 16, 18, 20].map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => setSize(s)}
          className={cn(
            'rounded-lg px-2.5 py-1 text-xs font-bold transition-all',
            size === s
              ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
              : 'glass text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]'
          )}
        >
          {s}px
        </button>
      ))}
    </div>
  );
}
