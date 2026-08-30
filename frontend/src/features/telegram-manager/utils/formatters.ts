/**
 * Telegram Formatters (Fixed)
 * ============================
 * Fixed: formatDateTime now properly handles invalid dates
 *
 * @module features/telegram-manager/utils
 */

/** Format large numbers with locale */
export function formatNumber(
  value: number,
  locale: string = 'en-US'
): string {
  return value.toLocaleString(locale);
}

/**
 * Format date for display.
 *
 * Fixed: Uses isNaN() to detect invalid dates (new Date('invalid')
 * doesn't throw, it returns Invalid Date).
 */
export function formatDateTime(
  dateString: string,
  locale: string = 'en-US'
): string {
  if (!dateString) return dateString;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString; // Invalid date → return as-is
  return date.toLocaleString(locale);
}

/** Format time only */
export function formatTime(date: Date, locale: string = 'en-US'): string {
  if (isNaN(date.getTime())) return '';
  return date.toLocaleTimeString(locale);
}
