import { type UseQueryOptions, useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { getApiClient } from '../client';
import {
  CarbonEstimate,
  CarbonEstimateRequest,
  CarbonProject,
} from '../schema/carbon';
import { queryKeys } from './query-keys';

const ProjectsResponse = z.object({ items: z.array(CarbonProject) });
const EstimateResponse = z.object({ estimate: CarbonEstimate });

export function useCarbonProjects(
  options?: Omit<UseQueryOptions<CarbonProject[]>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.carbon.projects(),
    queryFn: async () => {
      const data = await getApiClient().get('/carbon/projects', ProjectsResponse);
      return data.items;
    },
    ...options,
  });
}

export function useCarbonEstimate(
  req: CarbonEstimateRequest,
  options?: Omit<UseQueryOptions<CarbonEstimate>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: queryKeys.carbon.estimate(req),
    queryFn: async () => {
      const data = await getApiClient().post('/carbon/estimate', req, EstimateResponse);
      return data.estimate;
    },
    enabled: !!req.project_id,
    ...options,
  });
}