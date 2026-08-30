/**
 * useSecurityEvents Hook
 * =======================
 * React Query with built-in auto-refresh.
 *
 * KEY IMPROVEMENT: Uses React Query's refetchInterval instead of
 * manual setInterval, eliminating stale closure issues.
 *
 * @module features/security/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { SecurityEvent } from '../types';
import {
  QUERY_KEYS,
  AUTO_REFRESH_INTERVAL_MS,
  STALE_TIME_MS,
  RETRY_COUNT,
} from '../constants/config';
import { fetchSecurityEvents } from '../api/securityApi';

interface UseSecurityEventsOptions {
  autoRefresh?: boolean;
}

export function useSecurityEvents(options: UseSecurityEventsOptions = {}) {
  const { autoRefresh = true } = options;

  const query = useQuery<SecurityEvent[], Error>({
    queryKey: QUERY_KEYS.events,
    queryFn: fetchSecurityEvents,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: true,
    // KEY: React Query handles interval internally
    refetchInterval: autoRefresh ? AUTO_REFRESH_INTERVAL_MS : false,
  });

  return {
    events: query.data ?? [],
    isLoading: query.isLoading && !query.data,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    dataUpdatedAt: query.dataUpdatedAt,
  };
}
