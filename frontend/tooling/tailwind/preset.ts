import type { Config } from 'tailwindcss';
import typographyHelpers from './typography-helpers';

/**
 * Shared Tailwind preset for Eco Nojin apps.
 * Uses CSS-first tokens from `@eco/tailwind-preset/tokens.css` (consumed via @import).
 */
const config: Config = {
  darkMode: 'class',
  content: [],
  theme: {
    extend: {
      colors: {
        // Brand: Earth (terracotta)
        brand: {
          50: 'rgb(var(--color-brand-50) / <alpha-value>)',
          100: 'rgb(var(--color-brand-100) / <alpha-value>)',
          200: 'rgb(var(--color-brand-200) / <alpha-value>)',
          300: 'rgb(var(--color-brand-300) / <alpha-value>)',
          400: 'rgb(var(--color-brand-400) / <alpha-value>)',
          500: 'rgb(var(--color-brand-500) / <alpha-value>)',
          600: 'rgb(var(--color-brand-600) / <alpha-value>)',
          700: 'rgb(var(--color-brand-700) / <alpha-value>)',
          800: 'rgb(var(--color-brand-800) / <alpha-value>)',
          900: 'rgb(var(--color-brand-900) / <alpha-value>)',
          950: 'rgb(var(--color-brand-950) / <alpha-value>)',
        },
        // Sky (water & climate)
        sky: {
          50: 'rgb(var(--color-sky-50) / <alpha-value>)',
          100: 'rgb(var(--color-sky-100) / <alpha-value>)',
          200: 'rgb(var(--color-sky-200) / <alpha-value>)',
          300: 'rgb(var(--color-sky-300) / <alpha-value>)',
          400: 'rgb(var(--color-sky-400) / <alpha-value>)',
          500: 'rgb(var(--color-sky-500) / <alpha-value>)',
          600: 'rgb(var(--color-sky-600) / <alpha-value>)',
          700: 'rgb(var(--color-sky-700) / <alpha-value>)',
          800: 'rgb(var(--color-sky-800) / <alpha-value>)',
          900: 'rgb(var(--color-sky-900) / <alpha-value>)',
        },
        // Leaf (vegetation & growth)
        leaf: {
          50: 'rgb(var(--color-leaf-50) / <alpha-value>)',
          100: 'rgb(var(--color-leaf-100) / <alpha-value>)',
          200: 'rgb(var(--color-leaf-200) / <alpha-value>)',
          300: 'rgb(var(--color-leaf-300) / <alpha-value>)',
          400: 'rgb(var(--color-leaf-400) / <alpha-value>)',
          500: 'rgb(var(--color-leaf-500) / <alpha-value>)',
          600: 'rgb(var(--color-leaf-600) / <alpha-value>)',
          700: 'rgb(var(--color-leaf-700) / <alpha-value>)',
          800: 'rgb(var(--color-leaf-800) / <alpha-value>)',
          900: 'rgb(var(--color-leaf-900) / <alpha-value>)',
        },
        // Neutrals (warm-tinted)
        surface: {
          DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
          muted: 'rgb(var(--color-surface-muted) / <alpha-value>)',
          raised: 'rgb(var(--color-surface-raised) / <alpha-value>)',
          overlay: 'rgb(var(--color-surface-overlay) / <alpha-value>)',
          inverse: 'rgb(var(--color-surface-inverse) / <alpha-value>)',
          'inverse-muted': 'rgb(var(--color-surface-inverse-muted) / <alpha-value>)',
        },
        ink: {
          DEFAULT: 'rgb(var(--color-ink) / <alpha-value>)',
          muted: 'rgb(var(--color-ink-muted) / <alpha-value>)',
          subtle: 'rgb(var(--color-ink-subtle) / <alpha-value>)',
          inverse: 'rgb(var(--color-ink-inverse) / <alpha-value>)',
        },
        // Status
        success: 'rgb(var(--color-success) / <alpha-value>)',
        warning: 'rgb(var(--color-warning) / <alpha-value>)',
        danger: 'rgb(var(--color-danger) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        fa: ['var(--font-fa)'],
        mono: ['var(--font-mono)'],
        display: ['var(--font-display)'],
      },
      borderRadius: {
        xs: 'var(--radius-xs)',
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
        raised: 'var(--shadow-raised)',
        elevated: 'var(--shadow-elevated)',
        glow: 'var(--shadow-glow)',
        'glow-sky': 'var(--shadow-glow-sky)',
        inner: 'var(--shadow-inner)',
      },
      maxWidth: {
        content: 'var(--max-content-width)',
      },
      spacing: {
        header: 'var(--header-height)',
      },
      transitionTimingFunction: {
        'out-soft': 'var(--ease-out-soft)',
        'in-out-soft': 'var(--ease-in-out-soft)',
      },
      transitionDuration: {
        fast: 'var(--duration-fast)',
        base: 'var(--duration-base)',
        slow: 'var(--duration-slow)',
      },
      backgroundImage: {
        'gradient-brand': 'var(--gradient-brand)',
        'gradient-sky': 'var(--gradient-sky)',
        'gradient-hero': 'var(--gradient-hero)',
      },
    },
  },
  plugins: [typographyHelpers],
};

export default config;