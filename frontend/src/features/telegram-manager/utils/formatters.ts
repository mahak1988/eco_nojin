/**
 * Telegram Formatters
 * ====================
 * @module features/telegram-manager/utils
 */

/** Format large numbers with locale */
export function formatNumber(
  value: number,
  locale: string = 'en-US'
): string {
  return value.toLocaleString(locale);
}

/** Format date for display */
export function formatDateTime(
  dateString: string,
  locale: string = 'en-US'
): string {
  try {
    return new Date(dateString).toLocaleString(locale);
  } catch {
    return dateString;
  }
}

/** Format time only */
export function formatTime(
  date: Date,
  locale: string = 'en-US'
): string {
  return date.toLocaleTimeString(locale);
}
