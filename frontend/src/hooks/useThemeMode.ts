import { useEffect, useState } from 'react';

export type ThemeMode = 'light' | 'dark';

export function useThemeMode(): ThemeMode {
  const [mode, setMode] = useState<ThemeMode>(
    () => (localStorage.getItem('theme') as ThemeMode) || 'light'
  );
  useEffect(() => {
    const h = (e: Event) => {
      const d = (e as CustomEvent).detail as ThemeMode;
      if (d) setMode(d);
    };
    window.addEventListener('eco-theme-change', h);
    return () => window.removeEventListener('eco-theme-change', h);
  }, []);
  return mode;
}

export function toggleTheme() {
  const cur = (localStorage.getItem('theme') as ThemeMode) || 'light';
  const next: ThemeMode = cur === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  document.documentElement.setAttribute('data-theme', next);
  window.dispatchEvent(new CustomEvent('eco-theme-change', { detail: next }));
}
