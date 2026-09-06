/**
 * Locale-aware number formatters used across all scientific dashboards.
 * Default `locale` is read from the i18n package at runtime via the formatter factory.
 */

export function formatNumber(
  value: number,
  options: Intl.NumberFormatOptions = {},
  locale = 'en-US',
): string {
  return new Intl.NumberFormat(locale, options).format(value);
}

export function formatCompact(value: number, locale = 'en-US', fractionDigits = 1): string {
  return formatNumber(value, { notation: 'compact', maximumFractionDigits: fractionDigits }, locale);
}

export function formatPercent(value: number, locale = 'en-US', fractionDigits = 1): string {
  return formatNumber(value / 100, { style: 'percent', maximumFractionDigits: fractionDigits }, locale);
}

export function formatCurrency(
  value: number,
  currency = 'USD',
  locale = 'en-US',
): string {
  return formatNumber(value, { style: 'currency', currency }, locale);
}