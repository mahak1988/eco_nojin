/**
 * Shared constants used by both apps and design system.
 * Mirrors backend `engine/hydroma/core/constants.py` where applicable.
 */

export const APP_NAME = 'Eco Nojin';
export const APP_DESCRIPTION = 'Digital Twin for Landscape Restoration';

export const SUPPORTED_LOCALES = ['en', 'fa', 'ar', 'ur'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const RTL_LOCALES: readonly Locale[] = ['fa', 'ar', 'ur'];

export const DEFAULT_THEME = 'light';
export const THEMES = ['light', 'dark'] as const;
export type Theme = (typeof THEMES)[number];

/** Hydrological scientific constants. Match `engine/hydroma/core/constants.py`. */
export const SCI_CONSTANTS = {
  WATER_DENSITY: 1000, // kg/m³
  EARTH_G: 9.80665, // m/s²
  MANNING_DEFAULT: 0.035,
  DEFAULT_TIMESTEP_HOURS: 24,
} as const;

export const API_TIMEOUT_MS = 30_000;
export const API_VERSION = 'v1';
export const API_BASE_PATH = `/api/${API_VERSION}`;