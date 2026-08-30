/**
 * Order Status Helpers
 * =====================
 * @module features/marketplace/constants
 */

import type { OrderStatus } from '../types';
import { COMPLETED_STATUSES } from './config';

/** Check if order is pending */
export function isPendingOrder(status: OrderStatus): boolean {
  return status === 'pending';
}

/** Check if order is completed */
export function isCompletedOrder(status: OrderStatus): boolean {
  return COMPLETED_STATUSES.includes(status);
}

/** Normalize status string to OrderStatus */
export function normalizeOrderStatus(status: string | undefined): OrderStatus {
  if (!status) return 'unknown';
  const lower = status.toLowerCase();
  if (lower === 'pending') return 'pending';
  if (lower === 'confirmed') return 'confirmed';
  if (lower === 'completed') return 'completed';
  if (lower === 'cancelled') return 'cancelled';
  return 'unknown';
}
