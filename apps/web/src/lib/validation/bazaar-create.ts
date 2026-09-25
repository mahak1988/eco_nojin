import { z } from 'zod';

export const bazaarCreateSchema = z.object({
  name: z.string().trim().min(3).max(120),
  marketplaceType: z.enum(['cooperative', 'individual', 'farmers_market', 'mixed', 'other']),
  description: z.string().trim().min(10).max(2000),
  address: z.string().trim().min(3).max(500),
  location: z.string().trim().min(2).max(500),
  villageId: z.string().uuid(),
  acceptEcommerce: z.boolean().refine((value) => value),
  acceptTrading: z.boolean().refine((value) => value),
  rulesDocument: z.string().trim().min(10).max(2000),
  contactEmail: z.union([z.literal(''), z.email()]),
  contactPhone: z.string().trim().max(30),
});

export type BazaarCreateInput = z.infer<typeof bazaarCreateSchema>;
