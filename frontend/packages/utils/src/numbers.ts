/** استانداردسازی اعداد و ارقام — Persian-first, Intl-based */
const FA = '۰۱۲۳۴۵۶۷۸۹';
const AR = '٠١٢٣٤٥٦٧٨٩';

export function toFaDigits(input: string | number): string {
  const s = typeof input === 'number' ? input.toString() : input;
  return s.replace(/[0-9]/g, (d) => FA[Number(d)] ?? d);
}
export function toEnDigits(input: string): string {
  return input
    .replace(/[۰-۹]/g, (d) => String(FA.indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String(AR.indexOf(d)));
}

export interface NumOpts { locale?: string; decimals?: number; compact?: boolean; }

export function formatNumber(value: number, opts: NumOpts = {}): string {
  const { locale = 'fa-IR', decimals = 2, compact = false } = opts;
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: decimals,
    notation: compact ? 'compact' : 'standard',
  }).format(value);
}

export function formatCompact(value: number, locale = 'fa-IR', fractionDigits = 1): string {
  return formatNumber(value, { locale, compact: true, decimals: fractionDigits });
}

export function formatPercent(value: number, locale = 'fa-IR'): string {
  return `${formatNumber(value, { locale })}٪`;
}
export function formatCurrency(value: number, currency = 'USD', locale = 'fa-IR'): string {
  return new Intl.NumberFormat(locale, { style: 'currency', currency, maximumFractionDigits: 0 }).format(value);
}
export function formatUnit(value: number, unit: string, locale = 'fa-IR'): string {
  return `${formatNumber(value, { locale })} ${unit}`;
}
