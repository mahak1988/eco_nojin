/**
 * Legacy auth store (localStorage-backed).
 *
 * Kept for backward compatibility with components from Phase 1/2 that
 * still call `setSession` / `clear`. New code should use {@link useAuth}
 * (Supabase) instead.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthSession, AuthState } from './types';

type AuthActions = {
  setSession: (session: AuthSession | null) => void;
  clear: () => void;
  setError: (message: string | null) => void;
  setStatus: (status: AuthState['status']) => void;
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set) => ({
      session: null,
      status: 'idle',
      error: null,

      setSession: (session) => {
        if (typeof window !== 'undefined') {
          if (session) window.localStorage.setItem('eco_token', session.token);
          else window.localStorage.removeItem('eco_token');
        }
        set({
          session,
          status: session ? 'authenticated' : 'idle',
          error: null,
        });
      },

      clear: () => {
        if (typeof window !== 'undefined') {
          window.localStorage.removeItem('eco_token');
        }
        set({ session: null, status: 'idle', error: null });
      },

      setError: (message) => set({ error: message, status: message ? 'error' : 'idle' }),
      setStatus: (status) => set({ status }),
    }),
    {
      name: 'eco.auth',
      partialize: (state) => ({ session: state.session }),
      onRehydrateStorage: () => (state) => {
        if (typeof window !== 'undefined' && state?.session?.token) {
          window.localStorage.setItem('eco_token', state.session.token);
        }
      },
    },
  ),
);