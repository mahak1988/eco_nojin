/** Theme system — Light / Dark / System with localStorage persistence. */

import { createContext, useContext, useEffect, useState, type Dispatch, type SetStateAction } from 'react';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: Dispatch<SetStateAction<Theme>>;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);
const STORAGE_KEY = 'econojin-theme';

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored;
  } catch {
    // ignore
  }
  return 'system';
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initialTheme = getInitialTheme();
  const [theme, setThemeState] = useState<Theme>(initialTheme);
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(
    initialTheme === 'system' ? getSystemTheme() : initialTheme,
  );

  useEffect(() => {
    const root = document.documentElement;
    const effective = theme === 'system' ? getSystemTheme() : theme;
    setResolvedTheme(effective);

    root.classList.remove('light', 'dark');
    root.classList.add(effective);
    root.setAttribute('data-theme', effective);

    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // ignore
    }
  }, [theme]);

  useEffect(() => {
    if (theme !== 'system') return;

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const effective = mq.matches ? 'dark' : 'light';
      setResolvedTheme(effective);
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(effective);
      document.documentElement.setAttribute('data-theme', effective);
    };

    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme: setThemeState }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
