/**
 * Marketplace Formatters
 * ========================
 * @module features/marketplace/utils
 */

/** Format currency in IRR (Iranian Rial) */
export function formatCurrency(
  value: number,
  locale: string = 'fa-IR',
  maxDigits: number = 0
): string {
  return value.toLocaleString(locale, { maximumFractionDigits: maxDigits });
}

/** Get order amount (handles total vs amount field) */
export function getOrderAmount(order: {
  total?: number;
  amount?: number;
}): number {
  return order.total ?? order.amount ?? 0;
}

/** Truncate ID for display */
export function truncateId(
  id: string | undefined,
  length: number = 8,
  fallback: string = 'N/A'
): string {
  if (!id) return fallback;
  return id.length > length ? id.substring(0, length) : id;
}

/** Safe string extraction */
export function safeString(value: unknown, fallback: string = '-'): string {
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value || fallback;
  if (typeof value === 'number') return value.toString();
  return fallback;
}
