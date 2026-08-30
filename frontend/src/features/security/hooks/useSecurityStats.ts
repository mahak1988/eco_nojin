/**
 * useSecurityStats Hook
 * ======================
 * Computes all derived statistics with useMemo.
 *
 * KEY IMPROVEMENT: All O(n) operations memoized.
 * Previously recalculated on every render.
 *
 * @module features/security/hooks
 */

import { useMemo } from 'react';
import type { SecurityEvent, SecurityStats } from '../types';
import {
  computeHourlyData,
  calculateSecurityScore,
  getUniqueFailedIPs,
  filterByType,
} from '../utils/eventTransformers';
import { formatSuccessRate } from '../utils/formatters';

export function useSecurityStats(events: SecurityEvent[]): SecurityStats {
  return useMemo(() => {
    const successEvents = filterByType(events, 'Successful Login');
    const failedEvents = filterByType(events, 'Failed Login');

    return {
      totalEvents: events.length,
      successRate: formatSuccessRate(successEvents.length, events.length),
      successCount: successEvents.length,
      failedCount: failedEvents.length,
      uniqueFailedIPs: getUniqueFailedIPs(events),
      securityScore: calculateSecurityScore(failedEvents.length),
      hourlyData: computeHourlyData(events),
    };
  }, [events]);
}
