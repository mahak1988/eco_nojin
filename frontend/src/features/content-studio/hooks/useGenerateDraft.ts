/**
 * useGenerateDraft Hook (useMutation)
 * @module features/content-studio/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { ContentItem, GenerateDraftRequest } from '../types';
import { QUERY_KEYS } from '../constants/config';
import { generateDraft } from '../api/contentStudioApi';

export function useGenerateDraft() {
  const queryClient = useQueryClient();

  const mutation = useMutation<ContentItem, Error, GenerateDraftRequest>({
    mutationFn: generateDraft,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.content });
    },
  });

  return {
    generate: (request: GenerateDraftRequest) => mutation.mutate(request),
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
  };
}
