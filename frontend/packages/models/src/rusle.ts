import { z } from 'zod';
import type { ModelMeta } from './types';

export const RusleInput = z.object({
  rainfall_erosivity: z.number().nonnegative(),
  soil_erodibility: z.number().nonnegative(),
  slope_length_m: z.number().nonnegative(),
  slope_pct: z.number().nonnegative(),
  cover_factor: z.number().min(0).max(1),
  practice_factor: z.number().min(0).max(2).default(1),
});
export type RusleInput = z.infer<typeof RusleInput>;

export const RUSLE_META: ModelMeta = {
  id: 'rusle',
  name: 'RUSLE',
  domain: 'erosion',
  description: 'Revised Universal Soil Loss Equation — annual soil erosion (t/ha/yr).',
  version: '2015',
  source: 'real',
  avg_runtime_ms: 2,
};

/**
 * RUSLE = R × K × LS × C × P. Pure client-side preview.
 */
export function rusleCompute(input: RusleInput): number {
  const { rainfall_erosivity, soil_erodibility, slope_length_m, slope_pct, cover_factor, practice_factor } = input;
  const ls = computeLS(slope_length_m, slope_pct);
  return rainfall_erosivity * soil_erodibility * ls * cover_factor * practice_factor;
}

function computeLS(length: number, slopePct: number): number {
  const theta = Math.atan(slopePct / 100);
  const m = 0.4; // slope-length exponent (approx)
  return (length / 22.13) ** m * (65.41 * Math.sin(theta) + 4.56 * Math.sin(theta) + 0.065);
}