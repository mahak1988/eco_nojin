/**
 * EcoWallet Formatters
 * =====================
 * Type-safe formatting utilities.
 *
 * @module features/eco-wallet/utils
 */

/**
 * Safely convert any value to string (generic version).
 *
 * Unlike the original `any`-based version, this uses TypeScript's
 * unknown type for better type safety.
 */
export function safeString<T = unknown>(value: T, fallback: string = 'N/A'): string {
  if (value === null || value === undefined) return fallback;

  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toString();
  if (typeof value === 'boolean') return String(value);

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }

  return String(value);
}

/**
 * Format number with locale-specific separators.
 *
 * @param value - Number to format
 * @param locale - Locale code (default: 'fa-IR' for Persian)
 */
export function formatNumber(value: number | undefined, locale: string = 'fa-IR'): string {
  if (value === undefined || value === null) return '0';
  return value.toLocaleString(locale);
}

/**
 * Safely extract numeric value with fallback.
 */
export function safeNumber(value: number | undefined, fallback: number = 0): number {
  return typeof value === 'number' && !isNaN(value) ? value : fallback;
}
