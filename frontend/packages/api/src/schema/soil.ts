import { z } from 'zod';
import { GeoBoundsSchema } from './common';

export const SoilTextureSchema = z.enum([
  'sand',
  'loamy_sand',
  'sandy_loam',
  'loam',
  'silt_loam',
  'silt',
  'clay_loam',
  'silty_clay_loam',
  'sandy_clay',
  'silty_clay',
  'clay',
]);
export type SoilTexture = z.infer<typeof SoilTextureSchema>;

export const SoilLayerSchema = z.object({
  depth_cm: z.number().min(0).max(500),
  texture: SoilTextureSchema,
  organic_carbon_pct: z.number().min(0).max(100),
  bulk_density_g_cm3: z.number().min(0.1).max(2.5),
  ph: z.number().min(0).max(14),
  cec_cmol_kg: z.number().nonnegative().optional(),
  clay_pct: z.number().min(0).max(100).optional(),
  silt_pct: z.number().min(0).max(100).optional(),
  sand_pct: z.number().min(0).max(100).optional(),
});
export type SoilLayer = z.infer<typeof SoilLayerSchema>;

export const SoilSampleRequestSchema = z.object({
  bounds: GeoBoundsSchema,
  depth_cm: z.number().min(0).max(500),
  samples: z.number().int().positive().max(500),
});
export type SoilSampleRequest = z.infer<typeof SoilSampleRequestSchema>;

export const SoilProfileSchema = z.object({
  id: z.string(),
  bounds: GeoBoundsSchema,
  layers: z.array(SoilLayerSchema).min(1),
  source: z.enum(['soilgrids', 'cdse', 'manual']),
  fetched_at: z.string(),
});
export type SoilProfile = z.infer<typeof SoilProfileSchema>;

export const SoilLayer = SoilLayerSchema;
export const SoilSampleRequest = SoilSampleRequestSchema;
export const SoilProfile = SoilProfileSchema;