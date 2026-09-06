import { z } from 'zod';
import type { ModelMeta } from './types';

export const RothCInput = z.object({
  years: z.number().int().min(1).max(100).default(20),
  climate_zone: z.enum(['tropical', 'subtropical', 'temperate', 'boreal']),
  soil_clay_pct: z.number().min(0).max(100).default(20),
  initial_soc_t_ha: z.number().nonnegative().default(50),
  plant_inputs_t_ha_yr: z.number().nonnegative().default(5),
  farmyard_manure_t_ha_yr: z.number().nonnegative().default(0),
});
export type RothCInput = z.infer<typeof RothCInput>;

export const ROTH_META: ModelMeta = {
  id: 'rothc',
  name: 'RothC',
  domain: 'carbon',
  description: 'Soil organic carbon turnover model (UK Rothamsted). 26.4 compartment kinetics.',
  version: '6.0',
  source: 'real',
  avg_runtime_ms: 35,
};