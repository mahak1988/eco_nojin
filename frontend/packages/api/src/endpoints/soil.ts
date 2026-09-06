import { apiClient } from '../mutator';

export const soilApi = {
  analyze: async (params: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post('/soil/analyze', params);
    return data;
  },

  getHistory: async (farmId: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/soil/history/${farmId}`);
    return data;
  },

  getErosion: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/soil/erosion');
    return data;
  },
};