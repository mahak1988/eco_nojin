import { z } from 'zod';
import { apiClient } from '../mutator';

export const CarbonProjectSchema = z
  .object({
    id: z.string(),
    name: z.string(),
    region: z.string().optional(),
    area_ha: z.number().optional(),
    species: z.string().optional(),
    years: z.number().optional(),
    co2_tons: z.number().optional(),
    credits: z.number().optional(),
    status: z.enum(['draft', 'verified', 'issued', 'retired']).optional(),
    created_at: z.string().optional(),
    region_name: z.string().optional(),
  })
  .passthrough();
export type CarbonProject = z.infer<typeof CarbonProjectSchema>;

export const CarbonCalculateRequestSchema = z.object({
  area_ha: z.number().positive(),
  species: z.string().min(1),
  years: z.number().int().min(1).max(100),
  region: z.string().optional(),
});
export type CarbonCalculateRequest = z.infer<typeof CarbonCalculateRequestSchema>;

export const CarbonCalculateResponseSchema = z
  .object({
    co2_tons: z.number(),
    credits: z.number(),
    revenue_usd: z.number().optional(),
    methodology: z.string().optional(),
  })
  .passthrough();
export type CarbonCalculateResponse = z.infer<typeof CarbonCalculateResponseSchema>;

export const carbonApi = {
  calculate: async (request: CarbonCalculateRequest): Promise<CarbonCalculateResponse> => {
    const { data } = await apiClient.post('/carbon/calculate', request);
    return CarbonCalculateResponseSchema.parse(data);
  },

  getProjects: async (): Promise<CarbonProject[]> => {
    const { data } = await apiClient.get('/carbon/projects');
    return z.array(CarbonProjectSchema).parse(data);
  },

  getProject: async (projectId: string): Promise<CarbonProject> => {
    const { data } = await apiClient.get(`/carbon/projects/${projectId}`);
    return CarbonProjectSchema.parse(data);
  },

  getStandards: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/carbon/standards');
    return data;
  },

  getSpecies: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/carbon/species');
    return data;
  },

  verifyProject: async (projectId: string): Promise<unknown> => {
    const { data } = await apiClient.post(`/carbon/projects/${projectId}/verify`);
    return data;
  },

  issueCredits: async (projectId: string): Promise<unknown> => {
    const { data } = await apiClient.post(`/carbon/projects/${projectId}/issue`);
    return data;
  },

  getWallet: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/carbon/wallet');
    return data;
  },
};