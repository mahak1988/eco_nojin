import { z } from 'zod';

export const sessionUserSchema = z.object({
  id: z.string().min(1),
  email: z.email(),
  full_name: z.string().nullable().optional(),
  role: z.string().min(1),
  language: z.string().nullable().optional(),
  phone: z.string().nullable().optional(),
  country: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  avatar_url: z.url().nullable().optional(),
  is_email_verified: z.boolean(),
  is_active: z.boolean(),
  created_at: z.string(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string().min(1),
  refresh_token: z.string().min(1),
  token_type: z.string().optional(),
  user: sessionUserSchema,
});

export const loginSchema = z.object({
  email: z.email(),
  password: z.string().min(1).max(128),
});

export const registerSchema = z.object({
  email: z.email(),
  full_name: z.string().trim().min(2).max(100),
  password: z.string().min(8).max(128),
  role: z.enum(['farmer', 'researcher', 'organization', 'tourist', 'regular']).default('regular'),
  language: z.enum(['fa', 'en', 'ar']).default('fa'),
  accept_tos: z.literal(true),
  accept_privacy: z.literal(true),
});

export type SessionUser = z.infer<typeof sessionUserSchema>;
export type TokenResponse = z.infer<typeof tokenResponseSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
