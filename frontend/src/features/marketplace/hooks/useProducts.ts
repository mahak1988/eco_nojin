/**
 * useProducts Hook (React Query)
 * @module features/marketplace/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { Product } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchProducts } from '../api/marketplaceApi';

export function useProducts() {
  const query = useQuery<Product[], Error>({
    queryKey: QUERY_KEYS.products,
    queryFn: fetchProducts,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    products: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
