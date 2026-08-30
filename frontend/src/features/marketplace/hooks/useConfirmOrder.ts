/**
 * useConfirmOrder Hook (useMutation)
 * ===================================
 * React Query mutation for confirming orders.
 * Automatically invalidates orders query on success.
 *
 * @module features/marketplace/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { QUERY_KEYS } from '../constants/config';
import { confirmOrderApi } from '../api/marketplaceApi';

export function useConfirmOrder() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, string>({
    mutationFn: confirmOrderApi,
    onSuccess: () => {
      // Invalidate orders query to refetch updated list
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.orders });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.stats });
    },
  });

  return {
    confirm: (orderId: string) => mutation.mutate(orderId),
    confirmAsync: (orderId: string) => mutation.mutateAsync(orderId),
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
}
