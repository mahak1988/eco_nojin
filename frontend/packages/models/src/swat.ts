import { z } from 'zod';
import type { ModelMeta } from './types';

export const SwatInput = z.object({
  bounds: z.object({
    south: z.number(),
    west: z.number(),
    north: z.number(),
    east: z.number(),
  }),
  start: z.string(),
  end: z.string(),
  land_use: z.enum(['cropland', 'forest', 'pasture', 'urban', 'wetland']).default('cropland'),
  soil_profile_id: z.string().optional(),
});
export type SwatInput = z.infer<typeof SwatInput>;

export const SWAT_META: ModelMeta = {
  id: 'swat',
  name: 'SWAT+',
  domain: 'water',
  description:
    'Soil & Water Assessment Tool — daily hydrology, sediment, nutrient cycles on sub-basin scale.',
  version: '2018.4',
  source: 'external',
  externalBinary: 'swatplus',
  avg_runtime_ms: 1200,
};