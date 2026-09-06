import { type UseQueryOptions, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { getApiClient } from '../client';
import { InfiltrationResult, WaterBalanceRequest, WaterBalanceSeries } from '../schema/water';
import { queryKeys } from './query-keys';

const BalanceResponse = z.object({ series: WaterBalanceSeries });

export function useWaterBalance(
  req: WaterBalanceRequest,
  options?: Omit<UseQueryOptions<WaterBalanceSeries>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.water.balance(req),
    queryFn: async () => {
      const data = await getApiClient().post('/water/balance', req, BalanceResponse);
      return data.series;
    },
    ...options,
  });
}

export function useInfiltration(
  boundsKey: string,
  options?: Omit<UseQueryOptions<InfiltrationResult>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.water.infiltration(boundsKey),
    queryFn: () =>
      getApiClient().get(
        `/water/infiltration?boundsKey=${encodeURIComponent(boundsKey)}`,
        InfiltrationResult,
      ),
    ...options,
  });
}