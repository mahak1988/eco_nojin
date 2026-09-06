/**
 * Spacing tokens — kept in sync with Tailwind's `p-*`, `m-*`, `gap-*` utilities.
 *
 * Use Tailwind utilities in component code. These tokens are exposed for JS-only
 * calculations (e.g. inline styles, animations).
 */

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
} as const

export type SpacingName = keyof typeof spacing

/**
 * Numeric spacing scale (4px grid) for one-off JS usage.
 * Mirrors Tailwind defaults so `0` → `0`, `1` → `0.25rem`, etc.
 */
export const numericSpacing = {
  0: '0px',
  px: '1px',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  11: '2.75rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
  44: '11rem',
  48: '12rem',
  52: '13rem',
  56: '14rem',
  60: '15rem',
  64: '16rem',
  72: '18rem',
  80: '20rem',
  96: '24rem',
} as const

export type NumericSpacing = keyof typeof numericSpacing

/**
 * Semantic spacing aliases for common patterns.
 */
export const semanticSpacing = {
  componentXS: numericSpacing[1], // 4px — tight
  componentSM: numericSpacing[2], // 8px — compact
  componentMD: numericSpacing[3], // 12px — default
  componentLG: numericSpacing[4], // 16px — spacious
  componentXL: numericSpacing[6], // 24px — large
  sectionSM: numericSpacing[6], // 24px — between cards
  sectionMD: numericSpacing[8], // 32px — between groups
  sectionLG: numericSpacing[12], // 48px — page sections
  sectionXL: numericSpacing[16], // 64px — major sections
  pageMD: numericSpacing[12], // 48px — page margins
  pageLG: numericSpacing[16], // 64px — page margins
} as const

export type SemanticSpacingToken = keyof typeof semanticSpacing
