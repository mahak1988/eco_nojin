/**
 * usePublishItem Hook (useMutation)
 * @module features/content-studio/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { QUERY_KEYS } from '../constants/config';
import { publishContentItem } from '../api/contentStudioApi';

export function usePublishItem() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, string>({
    mutationFn: publishContentItem,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.content });
    },
  });

  return {
    publish: (id: string) => mutation.mutate(id),
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
}
