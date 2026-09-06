import { type UseQueryOptions, useQuery } from '@tanstack/react-query';
import { getApiClient } from '../client';
import { DashboardSnapshot } from '../schema/analytics';
import { queryKeys } from './query-keys';

export function useDashboardSnapshot(
  options?: Omit<UseQueryOptions<DashboardSnapshot>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.dashboardSnapshot(),
    queryFn: () => getApiClient().get('/dashboard/snapshot', DashboardSnapshot),
    staleTime: 60_000,
    refetchInterval: 5 * 60_000,
    ...options,
  });
}