/**
 * ContentStudio Formatters
 * ===========================
 * @module features/content-studio/utils
 */

/** Truncate ID for display */
export function truncateId(
  id: string | undefined,
  length: number = 8,
  fallback: string = 'N/A'
): string {
  if (!id) return fallback;
  return id.length > length ? id.substring(0, length) : id;
}

/** Format date for display */
export function formatDate(
  dateString: string | undefined,
  fallback: string = '-'
): string {
  if (!dateString) return fallback;
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return fallback;
  }
}

/** Normalize status for comparison */
export function normalizeStatus(status: string | undefined): string {
  return (status || '').toLowerCase();
}

/** Get status badge class */
export function getStatusBadgeClass(status: string | undefined): string {
  const normalized = normalizeStatus(status);
  if (normalized === 'published') return 'success';
  if (normalized === 'draft') return 'warning';
  return 'info';
}
