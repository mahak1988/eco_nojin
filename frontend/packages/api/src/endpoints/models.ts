import { z } from 'zod';
import { apiClient } from '../mutator';

export const ModelSchema = z
  .object({
    id: z.string(),
    name: z.string(),
    category: z.string().optional(),
    description: z.string().optional(),
    endpoint: z.string().optional(),
  })
  .passthrough();
export type Model = z.infer<typeof ModelSchema>;

export const MotorRunRequestSchema = z.object({
  motor: z.string(),
  inputs: z.record(z.unknown()),
});
export type MotorRunRequest = z.infer<typeof MotorRunRequestSchema>;

export const MotorRunResponseSchema = z
  .object({
    run_id: z.string().optional(),
    status: z.enum(['pending', 'running', 'completed', 'failed']).optional(),
    result: z.unknown().optional(),
    duration_ms: z.number().optional(),
    cached: z.boolean().optional(),
    output: z.record(z.unknown()).optional(),
    motor: z.string().optional(),
  })
  .passthrough();
export type MotorRunResponse = z.infer<typeof MotorRunResponseSchema>;

export const modelsApi = {
  getAll: async (): Promise<Model[]> => {
    const { data } = await apiClient.get('/models');
    return z.array(ModelSchema).parse(data);
  },

  getList: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/models/list');
    return data;
  },

  getModel: async (slug: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/models/${slug}`);
    return data;
  },

  runModel: async (slug: string, inputs: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post(`/models/${slug}/run`, { inputs });
    return data;
  },
};

export const motorsApi = {
  getList: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/motors/list');
    return data;
  },

  run: async (request: MotorRunRequest): Promise<MotorRunResponse> => {
    const { data } = await apiClient.post('/motors/run', request);
    return MotorRunResponseSchema.parse(data);
  },

  chain: async (chain: MotorRunRequest[]): Promise<unknown> => {
    const { data } = await apiClient.post('/motors/chain', { chain });
    return data;
  },

  getStatus: async (runId: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/motors/status/${runId}`);
    return data;
  },
};