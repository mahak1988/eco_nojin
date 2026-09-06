export function formatDate(
  value: Date | string | number,
  locale = 'en-US',
  options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: '2-digit' },
): string {
  const d = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat(locale, options).format(d);
}

export function formatDateTime(
  value: Date | string | number,
  locale = 'en-US',
): string {
  return formatDate(
    value,
    locale,
    { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' },
  );
}

export function formatRelative(
  value: Date | string | number,
  locale = 'en-US',
  now: Date = new Date(),
): string {
  const d = value instanceof Date ? value : new Date(value);
  const diff = (d.getTime() - now.getTime()) / 1000;
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  const abs = Math.abs(diff);
  if (abs < 60) return rtf.format(Math.round(diff), 'second');
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), 'hour');
  if (abs < 86400 * 30) return rtf.format(Math.round(diff / 86400), 'day');
  if (abs < 86400 * 365) return rtf.format(Math.round(diff / (86400 * 30)), 'month');
  return rtf.format(Math.round(diff / (86400 * 365)), 'year');
}