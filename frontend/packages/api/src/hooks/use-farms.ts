import {
  type UseMutationOptions,
  type UseQueryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { z } from 'zod';
import { getApiClient } from '../client';
import { Farm, type Farm as FarmT, FarmCreate } from '../schema/farms';
import { queryKeys } from './query-keys';

const FarmListResponse = z.object({ items: z.array(Farm) });

export function useFarms(options?: Omit<UseQueryOptions<FarmT[]>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: queryKeys.farms.list(),
    queryFn: async () => {
      const data = await getApiClient().get('/farms', FarmListResponse);
      return data.items;
    },
    ...options,
  });
}

export function useCreateFarm(
  options?: Omit<UseMutationOptions<FarmT, Error, FarmCreate>, 'mutationFn'>,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input) => getApiClient().post('/farms', input, Farm),
    onSuccess: (farm) => {
      qc.setQueryData<FarmT[]>(queryKeys.farms.list(), (prev) => (prev ? [...prev, farm] : [farm]));
      qc.invalidateQueries({ queryKey: queryKeys.farms.detail(farm.id) });
    },
    ...options,
  });
}