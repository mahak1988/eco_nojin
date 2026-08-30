/**
 * useMarketplaceStats Hook (React Query)
 * @module features/marketplace/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { MarketplaceStats } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchMarketplaceStats } from '../api/marketplaceApi';

export function useMarketplaceStats() {
  const query = useQuery<MarketplaceStats, Error>({
    queryKey: QUERY_KEYS.stats,
    queryFn: fetchMarketplaceStats,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    stats: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
