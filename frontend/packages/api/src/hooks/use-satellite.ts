import { type UseQueryOptions, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { getApiClient } from '../client';
import { GeoBounds } from '../schema/common';
import {
  SatelliteIndexRequest,
  SatelliteIndexSeries,
  SatelliteScene,
} from '../schema/satellite';
import { queryKeys } from './query-keys';

const ScenesResponse = z.object({ items: z.array(SatelliteScene) });
const SeriesResponse = z.object({ series: SatelliteIndexSeries });

export function useSatelliteScenes(
  bounds: GeoBounds,
  options?: Omit<UseQueryOptions<SatelliteScene[]>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.satellite.scenes(JSON.stringify(bounds)),
    queryFn: async () => {
      const data = await getApiClient().post('/satellite/scenes', { bounds }, ScenesResponse);
      return data.items;
    },
    ...options,
  });
}

export function useSatelliteIndexSeries(
  req: SatelliteIndexRequest,
  options?: Omit<UseQueryOptions<SatelliteIndexSeries>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.satellite.series(req),
    queryFn: async () => {
      const data = await getApiClient().post('/satellite/series', req, SeriesResponse);
      return data.series;
    },
    ...options,
  });
}