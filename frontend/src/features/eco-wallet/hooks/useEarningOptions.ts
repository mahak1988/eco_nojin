/**
 * useEarningOptions Hook
 * =======================
 * React Query hook for earning options.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { EarningOption } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchEarningOptions } from '../api/ecoWalletApi';

export function useEarningOptions() {
  const query = useQuery<EarningOption[], Error>({
    queryKey: QUERY_KEYS.earningOptions,
    queryFn: fetchEarningOptions,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    options: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
