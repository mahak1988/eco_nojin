/**
 * Supabase-backed Zustand auth store.
 *
 * Falls back to a "local stub" when env is not configured so the dashboard
 * can still render in demo mode (e.g. during development without Supabase).
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getSupabase } from './supabaseClient';
import type { User } from './types';

export type AuthStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated' | 'error';

export type AuthError = { code: string; message: string } | null;

export interface AuthState {
  user: User | null;
  status: AuthStatus;
  error: AuthError;
  isSupabaseConfigured: boolean;
  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Local dev fallback: pretend a user is signed in. */
  devSignIn: (user?: Partial<User>) => void;
}

function mapUser(u: { id: string; email?: string; user_metadata?: Record<string, unknown>; app_metadata?: Record<string, unknown> }): User {
  const roleRaw = u.app_metadata?.['role'];
  const validRoles: User['role'][] = ['admin', 'scientist', 'farmer', 'citizen', 'guest'];
  const role = (validRoles as string[]).includes(String(roleRaw))
    ? (roleRaw as User['role'])
    : 'citizen';
  return {
    id: u.id,
    email: u.email ?? '',
    full_name: (u.user_metadata?.['full_name'] as string | undefined) ?? '',
    role,
    avatar_url: u.user_metadata?.['avatar_url'] as string | undefined,
  };
}

function detectSupabaseConfigured(): boolean {
  if (typeof import.meta === 'undefined') return false;
  const env = (import.meta as { env?: Record<string, string | undefined> }).env ?? {};
  return Boolean(env['VITE_SUPABASE_URL'] && env['VITE_SUPABASE_ANON_KEY']);
}

const FALLBACK_USER: User = {
  id: 'demo-user',
  email: 'demo@eco-nojin.local',
  full_name: 'Demo User',
  role: 'scientist',
};

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      status: 'idle',
      error: null,
      isSupabaseConfigured: detectSupabaseConfigured(),

      initialize: async () => {
        set({ status: 'loading', error: null });
        if (!get().isSupabaseConfigured) {
          // Local stub mode — keep user null until explicit devSignIn.
          set({ status: 'unauthenticated' });
          return;
        }
        try {
          const supabase = getSupabase();
          const { data, error } = await supabase.auth.getSession();
          if (error) {
            set({ status: 'error', error: { code: 'init', message: error.message } });
            return;
          }
          set({
            user: data.session?.user ? mapUser(data.session.user) : null,
            status: data.session ? 'authenticated' : 'unauthenticated',
          });

          supabase.auth.onAuthStateChange((_event, session) => {
            set({
              user: session?.user ? mapUser(session.user) : null,
              status: session ? 'authenticated' : 'unauthenticated',
              error: null,
            });
          });
        } catch (err) {
          set({
            status: 'error',
            error: { code: 'init_throw', message: (err as Error).message },
          });
        }
      },

      signIn: async (email, password) => {
        if (!get().isSupabaseConfigured) {
          set({
            error: {
              code: 'no_supabase',
              message: 'Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.',
            },
          });
          throw new Error('Supabase not configured');
        }
        set({ status: 'loading', error: null });
        const { error } = await getSupabase().auth.signInWithPassword({ email, password });
        if (error) {
          set({ status: 'error', error: { code: 'signin', message: error.message } });
          throw error;
        }
      },

      signUp: async (email, password) => {
        if (!get().isSupabaseConfigured) {
          set({
            error: { code: 'no_supabase', message: 'Supabase is not configured.' },
          });
          throw new Error('Supabase not configured');
        }
        set({ status: 'loading', error: null });
        const { error } = await getSupabase().auth.signUp({ email, password });
        if (error) {
          set({ status: 'error', error: { code: 'signup', message: error.message } });
          throw error;
        }
      },

      signOut: async () => {
        try {
          if (get().isSupabaseConfigured) {
            await getSupabase().auth.signOut();
          }
        } finally {
          set({ user: null, status: 'unauthenticated', error: null });
        }
      },

      devSignIn: (user?: Partial<User>) => {
        set({
          user: { ...FALLBACK_USER, ...user },
          status: 'authenticated',
          error: null,
        });
      },
    }),
    {
      name: 'eco.auth',
      partialize: (state) => ({ user: state.user, status: state.status }),
    },
  ),
);