import { z } from 'zod';
import { GeoBoundsSchema } from './common';

export const FarmSchema = z.object({
  id: z.string(),
  name: z.string(),
  owner_id: z.string(),
  bounds: GeoBoundsSchema,
  centroid: z.object({ lat: z.number(), lon: z.number() }),
  area_ha: z.number().nonnegative(),
  primary_crop: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Farm = z.infer<typeof FarmSchema>;

export const FarmCreateSchema = z.object({
  name: z.string().min(2).max(120),
  bounds: GeoBoundsSchema,
  primary_crop: z.string().optional(),
});
export type FarmCreate = z.infer<typeof FarmCreateSchema>;

export const Farm = FarmSchema;
export const FarmCreate = FarmCreateSchema;