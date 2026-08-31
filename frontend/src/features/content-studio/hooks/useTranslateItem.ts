/**
 * useTranslateItem Hook (useMutation)
 * @module features/content-studio/hooks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { TranslateRequest } from '../types';
import { QUERY_KEYS } from '../constants/config';
import { translateContentItem } from '../api/contentStudioApi';

interface TranslateParams {
  id: string;
  request: TranslateRequest;
}

export function useTranslateItem() {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, Error, TranslateParams>({
    mutationFn: ({ id, request }) => translateContentItem(id, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.content });
    },
  });

  return {
    translate: (id: string, request: TranslateRequest) => mutation.mutate({ id, request }),
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
}
