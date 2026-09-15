import { useEffect, useState } from 'react';
import { Moon, Sun, Monitor } from 'lucide-react';
import { cn } from '../../lib/utils';

/** Auto theme toggle with system preference support. */
export default function AutoThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>('dark');

  useEffect(() => {
    const saved = localStorage.getItem('theme') as typeof theme | null;
    if (saved) setTheme(saved);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (!saved && prefersDark) setTheme('dark');
  }, []);

  const apply = (t: typeof theme) => {
    setTheme(t);
    localStorage.setItem('theme', t);
    if (t === 'auto') {
      const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.classList.toggle('dark', dark);
    } else {
      document.documentElement.classList.toggle('dark', t === 'dark');
    }
  };

  return (
    <div className="flex items-center gap-1 rounded-xl glass p-1">
      {[
        { key: 'light', icon: Sun, label: 'روشن' },
        { key: 'dark', icon: Moon, label: 'تاریک' },
        { key: 'auto', icon: Monitor, label: 'خودکار' },
      ].map(({ key, icon: Icon, label }) => (
        <button
          key={key}
          type="button"
          onClick={() => apply(key as typeof theme)}
          className={cn(
            'p-2 rounded-lg transition-all',
            theme === key
              ? 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-300)]'
              : 'text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]'
          )}
          title={label}
          aria-label={label}
        >
          <Icon className="h-4 w-4" aria-hidden />
        </button>
      ))}
    </div>
  );
}
