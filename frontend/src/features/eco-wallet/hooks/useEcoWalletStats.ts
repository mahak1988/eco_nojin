/**
 * useEcoWalletStats Hook
 * =======================
 * React Query hook for wallet statistics.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { WalletStats } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchWalletStats } from '../api/ecoWalletApi';

export function useEcoWalletStats() {
  const query = useQuery<WalletStats, Error>({
    queryKey: QUERY_KEYS.stats,
    queryFn: fetchWalletStats,
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
