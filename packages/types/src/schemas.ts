import { z } from 'zod';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  language: string;
  phone: string | null;
  country: string | null;
  city: string | null;
  avatar_url: string | null;
  is_email_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthSession {
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  user: UserProfile;
  source: 'local' | 'supabase';
}

export interface QueuedMutation {
  id?: number;
  endpoint: string;
  method: string;
  payload: unknown;
  idempotency_key?: string;
  timestamp: number;
  retryCount: number;
  status: 'pending' | 'processing' | 'failed';
  // Vector clock fields for conflict resolution
  entity_type?: string;
  entity_id?: string;
  vector_clock?: Record<string, number>;
  client_timestamp?: string;
  resolution_strategy?: 'server_wins' | 'client_wins' | 'merge' | 'manual';
}

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(100),
});

export const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(100),
  fullName: z.string().min(2).max(100),
  role: z.enum(['farmer', 'researcher', 'organization', 'tourist', 'regular']),
  language: z.enum(['fa', 'en', 'ar', 'tr']).default('fa'),
  acceptTos: z.literal(true),
  acceptPrivacy: z.literal(true),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email(),
});

export const resetPasswordSchema = z.object({
  token: z.string().min(1),
  newPassword: z.string().min(8).max(100),
});

export const featureFlagsSchema = z.object({
  enableSupabaseSync: z.boolean(),
  enableRealtimeSse: z.boolean(),
  enableDebugRoutes: z.boolean(),
});
