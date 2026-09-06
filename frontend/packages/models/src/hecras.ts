import { z } from 'zod';
import type { ModelMeta } from './types';

export const HecRasInput = z.object({
  cross_sections: z.array(
    z.object({
      station_m: z.number(),
      elevation_m: z.number(),
      manning_n: z.number().nonnegative().default(0.035),
    }),
  ),
  discharge_m3s: z.number().positive(),
  slope: z.number().nonnegative(),
});
export type HecRasInput = z.infer<typeof HecRasInput>;

export const HECRAS_META: ModelMeta = {
  id: 'hecras',
  name: 'HEC-RAS',
  domain: 'hydraulic',
  description: '1D steady/unsteady open-channel flow using Manning equation.',
  version: '6.5',
  source: 'external',
  externalBinary: 'HEC-RAS',
  avg_runtime_ms: 450,
};

/**
 * Manning uniform-flow approximation (client preview):
 * Q = (1/n) × A × R^(2/3) × S^(1/2)
 */
export function manningNormalDepth(input: HecRasInput): number {
  const { cross_sections, discharge_m3s, slope } = input;
  const A = cross_sections.reduce((acc, cs) => acc + cs.station_m * 1, 0); // area proxy
  const P = cross_sections.reduce((acc, cs) => acc + 1 + cs.station_m, 0);
  const R = A / Math.max(P, 1e-6);
  const n = cross_sections[0]?.manning_n ?? 0.035;
  const q = (1 / n) * A * Math.pow(R, 2 / 3) * Math.pow(slope, 0.5);
  return q - discharge_m3s; // residual for Newton iteration upstream
}