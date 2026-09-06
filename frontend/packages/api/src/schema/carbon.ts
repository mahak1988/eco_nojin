import { z } from 'zod';

export const CarbonStandardSchema = z.enum([
  'verra_vmd0007',
  'gold_standard',
  'plan_vivo',
  'car',
]);
export type CarbonStandard = z.infer<typeof CarbonStandardSchema>;

const PracticeSchema = z.enum([
  'agroforestry',
  'cover_crop',
  'reforestation',
  'biochar',
  'rewetting',
]);

export const CarbonProjectSchema = z.object({
  id: z.string(),
  name: z.string(),
  area_ha: z.number().nonnegative(),
  practice: PracticeSchema,
  standard: CarbonStandardSchema,
  start_year: z.number().int(),
  vintage: z.number().int(),
});
export type CarbonProject = z.infer<typeof CarbonProjectSchema>;

export const CarbonEstimateRequestSchema = z.object({
  project_id: z.string(),
  practice: PracticeSchema,
  area_ha: z.number().positive(),
  years: z.number().int().min(1).max(50),
  soc_baseline_t_ha: z.number().min(0).optional(),
  climate_zone: z.enum(['tropical', 'subtropical', 'temperate', 'boreal']),
});
export type CarbonEstimateRequest = z.infer<typeof CarbonEstimateRequestSchema>;

export const CarbonEstimateSchema = z.object({
  total_co2e_t: z.number(),
  annual_co2e_t: z.number(),
  uncertainty_pct: z.number().min(0).max(100),
  soc_trajectory: z.array(z.object({ year: z.number().int(), soc_t_ha: z.number() })),
  per_practice: z.record(z.string(), z.number()).optional(),
});
export type CarbonEstimate = z.infer<typeof CarbonEstimateSchema>;

export const CarbonStandard = CarbonStandardSchema;
export const CarbonProject = CarbonProjectSchema;
export const CarbonEstimateRequest = CarbonEstimateRequestSchema;
export const CarbonEstimate = CarbonEstimateSchema;