/**
 * useDeleteItem Hook (useMutation)
 * @module features/content-studio/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { QUERY_KEYS } from '../constants/config';
import { deleteContentItem } from '../api/contentStudioApi';

export function useDeleteItem() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, string>({
    mutationFn: deleteContentItem,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.content });
    },
  });

  return {
    delete: (id: string) => mutation.mutate(id),
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
}
