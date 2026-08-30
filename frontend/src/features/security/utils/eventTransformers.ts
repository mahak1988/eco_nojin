/**
 * Event Transformers
 * ===================
 * Pure functions for transforming security events into derived data.
 *
 * These are separated from the component for:
 * - Testability (pure functions)
 * - Memoization (useMemo with stable deps)
 * - Reusability
 *
 * @module features/security/utils
 */

import type { SecurityEvent, HourlyData } from '../types';
import { CHART_CONFIG, SECURITY_SCORE } from '../constants/config';

/**
 * Compute hourly aggregated data (O(n) complexity).
 *
 * Previously done inline in render (recalculated every render).
 * Now pure function for useMemo optimization.
 */
export function computeHourlyData(events: SecurityEvent[]): HourlyData[] {
  const currentHour = new Date().getHours();

  return Array.from({ length: CHART_CONFIG.hours }, (_, i) => {
    const hour = (currentHour - 23 + i + 24) % 24;
    const hourEvents = events.filter((e) => {
      if (!e.created_at) return false;
      const eventDate = new Date(e.created_at);
      return !isNaN(eventDate.getTime()) && eventDate.getHours() === hour;
    });

    return {
      hour: hour.toString().padStart(2, '0') + ':00',
      success: hourEvents.filter((e) => e.type === 'Successful Login').length,
      failed: hourEvents.filter((e) => e.type === 'Failed Login').length,
    };
  });
}

/**
 * Calculate security score based on failed events.
 */
export function calculateSecurityScore(failedCount: number): number {
  return Math.min(
    SECURITY_SCORE.base,
    Math.max(0, SECURITY_SCORE.base - failedCount * SECURITY_SCORE.failedPenalty)
  );
}

/**
 * Get unique failed IPs count.
 */
export function getUniqueFailedIPs(events: SecurityEvent[]): number {
  const uniqueIPs = new Set(
    events.filter((e) => e.type === 'Failed Login').map((e) => e.ip_address).filter(Boolean)
  );
  return uniqueIPs.size;
}

/**
 * Filter events by type (helper).
 */
export function filterByType(
  events: SecurityEvent[],
  type: SecurityEvent['type']
): SecurityEvent[] {
  return events.filter((e) => e.type === type);
}
