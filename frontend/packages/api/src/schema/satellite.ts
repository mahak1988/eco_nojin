import { z } from 'zod';
import { GeoBoundsSchema } from './common';

export const SatelliteSourceSchema = z.enum([
  'sentinel2',
  'sentinel1',
  'landsat8',
  'modis',
  'era5',
]);
export type SatelliteSource = z.infer<typeof SatelliteSourceSchema>;

export const SatelliteIndexNameSchema = z.enum(['NDVI', 'NDWI', 'EVI', 'LAI', 'SAVI']);

export const SatelliteSceneSchema = z.object({
  id: z.string(),
  source: SatelliteSourceSchema,
  acquired_at: z.string(),
  bounds: GeoBoundsSchema,
  cloud_cover_pct: z.number().min(0).max(100).optional(),
  indices: z.array(SatelliteIndexNameSchema),
});
export type SatelliteScene = z.infer<typeof SatelliteSceneSchema>;

export const SatelliteIndexRequestSchema = z.object({
  source: SatelliteSourceSchema,
  index: SatelliteIndexNameSchema,
  bounds: GeoBoundsSchema,
  start: z.string(),
  end: z.string(),
});
export type SatelliteIndexRequest = z.infer<typeof SatelliteIndexRequestSchema>;

export const SatelliteIndexSeriesSchema = z.object({
  values: z.array(
    z.object({ date: z.string(), value: z.number(), quality: z.number().min(0).max(1) }),
  ),
  unit: z.string(),
  summary: z.object({ min: z.number(), max: z.number(), mean: z.number(), std: z.number() }),
});
export type SatelliteIndexSeries = z.infer<typeof SatelliteIndexSeriesSchema>;

export const SatelliteSource = SatelliteSourceSchema;
export const SatelliteScene = SatelliteSceneSchema;
export const SatelliteIndexRequest = SatelliteIndexRequestSchema;
export const SatelliteIndexSeries = SatelliteIndexSeriesSchema;