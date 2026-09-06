import { apiClient } from '../mutator';

export const satelliteApi = {
  analyze: async (farmId: string, params: Record<string, unknown> = {}): Promise<unknown> => {
    const { data } = await apiClient.post('/satellite/analyze', { farm_id: farmId, ...params });
    return data;
  },

  getHistory: async (farmId: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/satellite/history/${farmId}`);
    return data;
  },

  getStats: async (farmId: string): Promise<unknown> => {
    const { data } = await apiClient.get(`/satellite/stats/${farmId}`);
    return data;
  },

  getWeather: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/satellite/weather');
    return data;
  },

  getEra5Series: async (params: Record<string, unknown>): Promise<unknown> => {
    const { data } = await apiClient.post('/satellite/era5/series', params);
    return data;
  },
};