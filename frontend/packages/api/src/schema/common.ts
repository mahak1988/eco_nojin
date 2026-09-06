import { z } from 'zod';

export const GeoPointSchema = z.object({
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
});
export type GeoPoint = z.infer<typeof GeoPointSchema>;

export const GeoBoundsSchema = z.object({
  south: z.number(),
  west: z.number(),
  north: z.number(),
  east: z.number(),
});
export type GeoBounds = z.infer<typeof GeoBoundsSchema>;

export const PaginationSchema = z.object({
  page: z.number().int().nonnegative().default(0),
  size: z.number().int().positive().max(200).default(25),
});
export type Pagination = z.infer<typeof PaginationSchema>;

export const UnitSystemSchema = z.enum(['metric', 'imperial']);
export type UnitSystem = z.infer<typeof UnitSystemSchema>;

export const ISODateSchema = z.string().datetime({ offset: true });
export type ISODate = z.infer<typeof ISODateSchema>;

/**
 * Back-compat: legacy callers may have imported the value named `GeoBounds`.
 * The actual schema lives at `GeoBoundsSchema`.
 */
export const GeoBounds = GeoBoundsSchema;