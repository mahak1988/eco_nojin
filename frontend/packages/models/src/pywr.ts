import { z } from 'zod';
import type { ModelMeta } from './types';

export const PywrInput = z.object({
  nodes: z.array(
    z.object({
      id: z.string(),
      type: z.enum(['catchment', 'reservoir', 'demand', 'junction']),
      capacity_m3: z.number().optional(),
      demand_m3: z.number().optional(),
    }),
  ),
  edges: z.array(z.object({ from: z.string(), to: z.string() })),
  timesteps: z.number().int().positive().default(365),
});
export type PywrInput = z.infer<typeof PywrInput>;

export const PYWR_META: ModelMeta = {
  id: 'pywr',
  name: 'Pywr',
  domain: 'water',
  description: 'Water resource network simulation (reservoirs, demands, allocations).',
  version: '2.0',
  source: 'real',
  avg_runtime_ms: 220,
};