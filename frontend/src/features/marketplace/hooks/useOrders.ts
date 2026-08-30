/**
 * useOrders Hook (React Query)
 * @module features/marketplace/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { Order } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchOrders } from '../api/marketplaceApi';

export function useOrders() {
  const query = useQuery<Order[], Error>({
    queryKey: QUERY_KEYS.orders,
    queryFn: fetchOrders,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    orders: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
