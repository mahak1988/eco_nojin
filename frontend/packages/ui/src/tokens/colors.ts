/**
 * Semantic colour palette for Eco Nojin.
 *
 * Three scientific domain palettes (`soil`, `water`, `carbon/vegetation`) are
 * intentionally aliased to Tailwind's `brand`, `sky`, `leaf` ramps so the
 * CSS variables defined in `tooling/tailwind/tokens.css` are the single source
 * of truth. Add `soil`, `water`, `carbon`, `vegetation`, `climate`, `satellite`
 * aliases for ergonomic imports in app code.
 */

export const colors = {
  primary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  /** Soil / earth tones — for terrestrial, soil-carbon contexts. */
  carbon: '#10b981',
  /** Water / sky tones — for hydrology, climate. */
  water: '#0ea5e9',
  /** Soil brown — for land-classification themes. */
  soil: '#a16207',
  /** Climate / warning tones. */
  climate: '#f59e0b',
  /** Satellite / remote-sensing tones. */
  satellite: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
} as const

export type ColorName = keyof typeof colors

/**
 * Semantic tokens — preferred way to refer to colours in app code.
 *
 * `soil`        = soil / earth
 * `water`       = hydrology / sky
 * `carbon`      = carbon stocks / credits
 * `vegetation`  = NDVI / biomass (alias of carbon for now)
 * `climate`     = drought / projection / warning
 * `satellite`   = Sentinel-2 / remote-sensing (alias of satellite)
 * `success`     = positive indicator
 * `warning`     = caution
 * `danger`      = error / destructive
 * `info`        = neutral information
 * `neutral`     = grayscale
 *
 * Each semantic token maps to a single base hex plus a ramp hint for theming.
 */
export const semanticTokens = {
  soil: '#a16207',
  water: '#0ea5e9',
  carbon: '#16a34a',
  vegetation: '#22c55e',
  climate: '#f59e0b',
  satellite: '#9333ea',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  neutral: '#6b7280',
} as const

export type SemanticToken = keyof typeof semanticTokens

/**
 * Tailwind utility names that match the semantic tokens.
 *
 * E.g. `tokenToTextClass('soil', 600)` → `'text-brand-700'` (because the
 * underlying CSS variable for `brand-700` mirrors soil-700).
 */
export function tokenToBgClass(
  token: SemanticToken,
  shade: 50 | 100 | 500 | 600 | 700 = 600,
): string {
  const map: Record<SemanticToken, string> = {
    soil: 'brand',
    water: 'sky',
    carbon: 'leaf',
    vegetation: 'leaf',
    climate: 'warning',
    satellite: 'satellite',
    success: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'info',
    neutral: 'ink',
  }
  // Neutral maps to ink ramp; everything else has its own ramp.
  const ramp = map[token]
  return `bg-${ramp}-${shade}`
}

export function tokenToTextClass(
  token: SemanticToken,
  shade: 50 | 100 | 500 | 600 | 700 = 700,
): string {
  const map: Record<SemanticToken, string> = {
    soil: 'brand',
    water: 'sky',
    carbon: 'leaf',
    vegetation: 'leaf',
    climate: 'warning',
    satellite: 'satellite',
    success: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'info',
    neutral: 'ink',
  }
  return `text-${map[token]}-${shade}`
}
