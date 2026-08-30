/**
 * useRedemptionOptions Hook
 * ===========================
 * React Query hook for redemption options.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { RedemptionOption } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchRedemptionOptions } from '../api/ecoWalletApi';

export function useRedemptionOptions() {
  const query = useQuery<RedemptionOption[], Error>({
    queryKey: QUERY_KEYS.redemptionOptions,
    queryFn: fetchRedemptionOptions,
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
