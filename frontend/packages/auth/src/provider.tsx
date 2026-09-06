import { type ReactNode, useEffect } from 'react';
import { TooltipProvider, ToastProvider } from '@eco/ui';
import { useAuthStore } from './store';

/**
 * Wraps the app with cross-cutting providers (tooltips, toasts).
 * Hydrates auth state from storage on mount.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const { session, setSession } = useAuthStore.getState();
    if (session) setSession(session);
  }, []);

  return (
    <TooltipProvider delayDuration={150}>
      <ToastProvider>{children}</ToastProvider>
    </TooltipProvider>
  );
}