/**
 * Security Formatters
 * ====================
 * @module features/security/utils
 */

/** Get security score color */
export function getScoreColor(score: number): string {
  if (score > 80) return 'var(--accent-primary)';
  if (score > 50) return 'var(--accent-secondary)';
  return 'var(--accent-danger)';
}

/** Format date for display */
export function formatEventTime(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return '-';
  return date.toLocaleString();
}

/** Format success rate */
export function formatSuccessRate(okCount: number, total: number): string {
  if (total === 0) return '0';
  return ((okCount / total) * 100).toFixed(1);
}
