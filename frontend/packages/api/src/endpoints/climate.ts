import { apiClient } from '../mutator';

export const climateApi = {
  analyzeDrought: async (params: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post('/climate/drought', params);
    return data;
  },

  analyze: async (params: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post('/climate', params);
    return data;
  },

  calibrate: async (params: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post('/climate/calibrate', params);
    return data;
  },
};