/**
 * Dashboard endpoints.
 *
 * The backend exposes both authenticated (`/api/v1/dashboard/*`) and public
 * (`/api/v1/dashboard/public/*`) routes. Schemas here are deliberately
 * permissive — extra fields are tolerated so older clients don't break when
 * the backend adds new keys.
 */
import { z } from 'zod';
import { apiClient } from '../mutator';

export const DashboardOverviewSchema = z
  .object({
    total_projects: z.number().optional(),
    total_area_hectares: z.number().optional(),
    carbon_credits: z.number().optional(),
    active_models: z.number().optional(),
    recent_activity: z
      .array(
        z.object({
          id: z.string(),
          action: z.string(),
          timestamp: z.string(),
        }),
      )
      .optional(),
  })
  .passthrough();

export type DashboardOverview = z.infer<typeof DashboardOverviewSchema>;

export const DashboardFullSchema = z
  .object({
    status: z.string().optional(),
    timestamp: z.string().optional(),
    auth_required: z.boolean().optional(),
    projects: z
      .object({
        total: z.number().optional(),
        total_area_hectares: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    weather: z
      .object({
        days_recorded: z.number().optional(),
        avg_temperature_max_c: z.number().optional(),
        avg_temperature_min_c: z.number().optional(),
        avg_temperature_c: z.number().optional(),
        total_rainfall_mm: z.number().optional(),
        avg_humidity_pct: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    satellite: z
      .object({
        total_images: z.number().optional(),
        avg_ndvi: z.number().optional(),
        avg_evi: z.number().optional(),
        avg_soil_moisture_index: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    soil: z
      .object({
        total_profiles: z.number().optional(),
        avg_organic_carbon_pct: z.number().optional(),
        avg_ph: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    carbon: z
      .object({
        total_credits: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    mrv: z
      .object({
        total_observations: z.number().optional(),
        verified_observations: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    simulations: z
      .object({
        total_runs: z.number().optional(),
        completed_runs: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    tourism: z
      .object({
        total_bookings: z.number().optional(),
        total_revenue: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
    platform: z
      .object({
        total_tables: z.number().optional(),
        active_motors: z.number().optional(),
        total_services: z.number().optional(),
        api_endpoints: z.number().optional(),
        status: z.string().optional(),
      })
      .passthrough()
      .optional(),
  })
  .passthrough();

export type DashboardFull = z.infer<typeof DashboardFullSchema>;

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const { data } = await apiClient.get('/dashboard/overview');
    return DashboardOverviewSchema.parse(data);
  },

  getFullDashboard: async (): Promise<DashboardFull> => {
    const { data } = await apiClient.get('/dashboard/public/full');
    return DashboardFullSchema.parse(data);
  },

  getProjects: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/projects');
    return data;
  },

  getCarbon: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/carbon');
    return data;
  },

  getWeather: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/weather');
    return data;
  },

  getSatellite: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/satellite');
    return data;
  },

  getSoil: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/soil');
    return data;
  },

  getMrv: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/mrv');
    return data;
  },

  getSimulations: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/simulations');
    return data;
  },

  getTourism: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/dashboard/public/tourism');
    return data;
  },
};