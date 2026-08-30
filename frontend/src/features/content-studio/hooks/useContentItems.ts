/**
 * useContentItems Hook (React Query)
 * @module features/content-studio/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { ContentItem } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchContentItems } from '../api/contentStudioApi';

export function useContentItems() {
  const query = useQuery<ContentItem[], Error>({
    queryKey: QUERY_KEYS.content,
    queryFn: fetchContentItems,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    items: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
