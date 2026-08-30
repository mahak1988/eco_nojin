/**
 * Marketplace Configuration
 * ===========================
 * @module features/marketplace/constants
 */

import type { OrderStatus } from '../types';

/** API base URL */
export const API_BASE =
  (typeof import.meta !== 'undefined' &&
    (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
      ?.VITE_API_BASE) ||
  'http://localhost:8000/api/v1';

/** API endpoints */
export const ENDPOINTS = {
  products: `${API_BASE}/marketplace/products`,
  orders: `${API_BASE}/marketplace/orders`,
  stats: `${API_BASE}/marketplace/stats`,
  confirmOrder: (orderId: string) =>
    `${API_BASE}/marketplace/orders/${orderId}/confirm`,
} as const;

/** React Query keys */
export const QUERY_KEYS = {
  products: ['marketplace', 'products'] as const,
  orders: ['marketplace', 'orders'] as const,
  stats: ['marketplace', 'stats'] as const,
} as const;

/** Chart colors for pie chart */
export const CHART_COLORS = [
  '#10b981',
  '#f59e0b',
  '#3b82f6',
  '#8b5cf6',
  '#ef4444',
] as const;

/** Display limits */
export const LIMITS = {
  pendingOrdersDisplay: 5,
  productsTableDisplay: 10,
} as const;

/** Statuses considered as "completed" */
export const COMPLETED_STATUSES: OrderStatus[] = ['confirmed', 'completed'];

/** React Query stale time (3 minutes for marketplace data) */
export const STALE_TIME_MS = 3 * 60 * 1000;

/** React Query retry count */
export const RETRY_COUNT = 2;
