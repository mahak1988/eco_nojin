'use client';
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  colors: typeof lightColors;
}

/*
 * Psychology of colors:
 * - Orange (#f97316): Warmth, hope, creativity, human connection
 * - Sky blue (#0ea5e9): Trust, clarity, openness, sky/water (life sources)
 * - Amber (#fbbf24): Sunshine, optimism, energy
 * - Deep teal (#0d9488): Balance between blue and green (earth+water)
 */
export const lightColors = {
  bg: '#fffbeb',  // warm cream
  bgAlt: '#ffffff',
  bgGradient: 'linear-gradient(135deg, #fef3c7 0%, #e0f2fe 100%)',
  text: '#1c1917',
  textMuted: '#78716c',
  primary: '#f97316',      // warm orange
  primaryLight: '#fb923c', // light orange
  primaryDark: '#ea580c',  // deep orange
  accent: '#0ea5e9',       // sky blue
  accentLight: '#38bdf8',  // light sky blue
  accentDark: '#0284c7',   // deep sky blue
  warm: '#fbbf24',         // amber
  cool: '#0ea5e9',         // sky blue
  calm: '#0d9488',         // teal (earth+water balance)
  border: '#fed7aa',       // orange border
  cardBg: 'rgba(255, 255, 255, 0.85)',
  cardBorder: 'rgba(249, 115, 22, 0.2)',
  shadow: '0 8px 32px rgba(249, 115, 22, 0.12)',
  shadowHover: '0 16px 48px rgba(14, 165, 233, 0.20)',
  glass: 'rgba(255, 251, 235, 0.8)',
  success: '#16a34a',
  warning: '#f59e0b',
  danger: '#dc2626',
  info: '#0ea5e9',
};

export const darkColors = {
  bg: '#0c0a09',  // warm dark
  bgAlt: '#1c1917',
  bgGradient: 'linear-gradient(135deg, #1c1917 0%, #082f49 100%)',
  text: '#fef3c7',
  textMuted: '#a8a29e',
  primary: '#fb923c',      // light orange (visible in dark)
  primaryLight: '#fdba74',
  primaryDark: '#f97316',
  accent: '#38bdf8',       // light sky blue
  accentLight: '#7dd3fc',
  accentDark: '#0ea5e9',
  warm: '#fbbf24',
  cool: '#38bdf8',
  calm: '#2dd4bf',
  border: '#78350f',       // dark orange
  cardBg: 'rgba(28, 25, 23, 0.85)',
  cardBorder: 'rgba(251, 146, 60, 0.25)',
  shadow: '0 8px 32px rgba(251, 146, 60, 0.15)',
  shadowHover: '0 16px 48px rgba(56, 189, 248, 0.25)',
  glass: 'rgba(28, 25, 23, 0.8)',
  success: '#22c55e',
  warning: '#fbbf24',
  danger: '#f87171',
  info: '#38bdf8',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    const saved = localStorage.getItem('theme') as Theme;
    if (saved) setTheme(saved);
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    document.body.style.background = theme === 'dark' ? darkColors.bg : lightColors.bg;
    document.body.style.color = theme === 'dark' ? darkColors.text : lightColors.text;
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');
  const colors = theme === 'dark' ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, colors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
