/**
 * Typography tokens for Eco Nojin.
 *
 * - **Numeric scale** (xs..3xl): 7 standard sizes. Use these as the canonical scale.
 * - **Legacy scale** (xs..5xl): kept for backward-compat; consider migrating to semantic.
 * - **Semantic classes**: heading/body/label utilities that map to a canonical scale.
 */

export const typography = {
  fontFamily: {
    sans: ['Vazirmatn', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
  /** Canonical 7-step numeric scale (Phase 3.2). */
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    /** @deprecated prefer the 7-step scale above. Kept for backward compat. */
    '4xl': '2.25rem',
    /** @deprecated prefer the 7-step scale above. Kept for backward compat. */
    '5xl': '3rem',
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
} as const

export type TypographyName = keyof typeof typography.fontFamily
export type FontSizeToken = keyof typeof typography.fontSize
export type FontWeightToken = keyof typeof typography.fontWeight

/**
 * Semantic mapping from display role → canonical size.
 * Use these in component APIs instead of arbitrary sizes.
 */
export const semanticTypography = {
  display: '3xl', // hero / page title
  h1: '3xl',
  h2: '2xl',
  h3: 'xl',
  h4: 'lg',
  bodyLg: 'lg',
  body: 'base',
  bodySm: 'sm',
  caption: 'xs',
  overline: 'xs',
} as const

export type SemanticTypographyRole = keyof typeof semanticTypography

/**
 * Tailwind class strings for each semantic role. Pre-built for ergonomic use
 * in components (e.g. `<h1 className={roleClasses.h1}>`).
 */
export const roleClasses = {
  display: 'text-3xl font-bold tracking-tight',
  h1: 'text-3xl font-bold tracking-tight',
  h2: 'text-2xl font-semibold tracking-tight',
  h3: 'text-xl font-semibold',
  h4: 'text-lg font-medium',
  bodyLg: 'text-lg leading-relaxed',
  body: 'text-base leading-relaxed',
  bodySm: 'text-sm leading-relaxed',
  caption: 'text-xs text-ink-muted',
  overline: 'text-xs font-semibold uppercase tracking-wide text-ink-muted',
} as const

export type TypographyRole = keyof typeof roleClasses
