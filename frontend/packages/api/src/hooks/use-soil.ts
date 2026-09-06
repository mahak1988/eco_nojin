import { type UseQueryOptions, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { getApiClient } from '../client';
import { GeoBounds } from '../schema/common';
import { SoilProfile, type SoilProfile as SoilProfileT } from '../schema/soil';
import { queryKeys } from './query-keys';

const SoilProfileResponse = z.object({ profile: SoilProfile });

export function useSoilProfile(
  bounds: GeoBounds,
  options?: Omit<UseQueryOptions<SoilProfileT>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.soil.profile(JSON.stringify(bounds)),
    queryFn: async () => {
      const data = await getApiClient().post('/soil/profile', { bounds }, SoilProfileResponse);
      return data.profile;
    },
    ...options,
  });
}