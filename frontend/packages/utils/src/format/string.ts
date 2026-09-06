export function truncate(text: string, max = 80, suffix = '…'): string {
  if (text.length <= max) return text;
  return `${text.slice(0, Math.max(0, max - suffix.length))}${suffix}`;
}

export function slugify(input: string): string {
  return input
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function titleCase(input: string): string {
  return input.replace(/\w\S*/g, (t) => t.charAt(0).toUpperCase() + t.slice(1).toLowerCase());
}