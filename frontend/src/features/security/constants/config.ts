/**
 * Security Configuration
 * =======================
 * @module features/security/constants
 */

/** API base URL */
export const API_BASE =
  (typeof import.meta !== 'undefined' &&
    (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
      ?.VITE_API_BASE) ||
  'http://localhost:8000/api/v1';

/** API endpoint */
export const ENDPOINTS = {
  security: `${API_BASE}/admin/security`,
} as const;

/** React Query keys */
export const QUERY_KEYS = {
  events: ['security', 'events'] as const,
} as const;

/** Auto-refresh interval (ms) */
export const AUTO_REFRESH_INTERVAL_MS = 10000;

/** Chart configuration */
export const CHART_CONFIG = {
  hours: 24,
  maxRecentEvents: 10,
} as const;

/** Security score calculation */
export const SECURITY_SCORE = {
  base: 100,
  failedPenalty: 5,
  goodThreshold: 80,
  warningThreshold: 50,
} as const;

/** React Query stale time */
export const STALE_TIME_MS = 30 * 1000; // 30s for real-time security data

/** React Query retry count */
export const RETRY_COUNT = 2;
