/**
 * EcoWallet Configuration
 * ========================
 * API endpoints, chart settings, and other configuration.
 *
 * @module features/eco-wallet/constants
 */

import type { ChartConfig } from '../types';

/** API base URL (from env or fallback) */
export const API_BASE =
  (typeof import.meta !== 'undefined' &&
    (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
      ?.VITE_API_BASE) ||
  'http://localhost:8000/api/v1';

/** API endpoints */
export const ENDPOINTS = {
  stats: `${API_BASE}/ecowallet/stats`,
  earningOptions: `${API_BASE}/ecowallet/earning-options`,
  redemptionOptions: `${API_BASE}/ecowallet/redemption-options`,
} as const;

/** React Query keys */
export const QUERY_KEYS = {
  stats: ['ecowallet', 'stats'] as const,
  earningOptions: ['ecowallet', 'earning-options'] as const,
  redemptionOptions: ['ecowallet', 'redemption-options'] as const,
} as const;

/** Transaction chart configuration */
export const CHART_CONFIG: ChartConfig = {
  days: 30,
  earningsRange: { min: 1000, max: 5000 },
  redemptionsRange: { min: 500, max: 3000 },
};

/** Chart colors */
export const CHART_COLORS = {
  earnings: '#10b981',
  redemptions: '#8b5cf6',
} as const;

/** React Query stale time (5 minutes) */
export const STALE_TIME_MS = 5 * 60 * 1000;

/** React Query retry count */
export const RETRY_COUNT = 2;
