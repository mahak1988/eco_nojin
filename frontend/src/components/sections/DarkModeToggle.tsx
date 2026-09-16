import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../theme/ThemeProvider';

/** Dark/light mode toggle — wired to the global ThemeProvider. */
export default function DarkModeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className="inline-flex h-9 w-9 items-center justify-center rounded-full glass glass-hover text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  );
}
