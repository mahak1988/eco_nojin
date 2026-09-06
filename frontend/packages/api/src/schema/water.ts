import { z } from 'zod';
import { GeoBoundsSchema } from './common';

export const WaterBalanceRequestSchema = z.object({
  bounds: GeoBoundsSchema,
  start: z.string(),
  end: z.string(),
  timestep: z.enum(['daily', 'monthly', 'yearly']),
});
export type WaterBalanceRequest = z.infer<typeof WaterBalanceRequestSchema>;

export const WaterBalanceSeriesSchema = z.object({
  timestamps: z.array(z.string()),
  precipitation_mm: z.array(z.number()),
  et0_mm: z.array(z.number()),
  runoff_mm: z.array(z.number()),
  recharge_mm: z.array(z.number()),
  storage_mm: z.array(z.number()),
});
export type WaterBalanceSeries = z.infer<typeof WaterBalanceSeriesSchema>;

export const InfiltrationResultSchema = z.object({
  fc_mm: z.number(),
  wp_mm: z.number(),
  ksat_mm_h: z.number(),
  initial_loss_mm: z.number(),
  curve_number: z.number().min(0).max(100),
});
export type InfiltrationResult = z.infer<typeof InfiltrationResultSchema>;

export const WaterBalanceRequest = WaterBalanceRequestSchema;
export const WaterBalanceSeries = WaterBalanceSeriesSchema;
export const InfiltrationResult = InfiltrationResultSchema;