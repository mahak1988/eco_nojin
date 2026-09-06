import { z } from 'zod';
import type { ModelMeta } from './types';

export const AquaCropInput = z.object({
  crop: z.enum(['wheat', 'maize', 'rice', 'barley', 'sorghum']),
  start: z.string(),
  end: z.string(),
  irrigation: z.enum(['full', 'deficit', 'rainfed']).default('rainfed'),
  soil_id: z.string().optional(),
});
export type AquaCropInput = z.infer<typeof AquaCropInput>;

export const AQUACROP_META: ModelMeta = {
  id: 'aquacrop',
  name: 'AquaCrop',
  domain: 'crop',
  description: 'FAO crop-water productivity model; daily biomass/yield under water stress.',
  version: '7.1',
  source: 'external',
  externalBinary: 'aquacrop',
  avg_runtime_ms: 35,
};