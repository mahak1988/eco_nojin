import { useEffect, type ReactNode } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '@eco/auth';
import { Spinner } from '@eco/ui';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const status = useAuth((s) => s.status);
  const initialize = useAuth((s) => s.initialize);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  useEffect(() => {
    if (status === 'unauthenticated') {
      void navigate({ to: '/login' });
    }
  }, [status, navigate]);

  if (status === 'idle' || status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-muted">
        <Spinner size="lg" />
      </div>
    );
  }

  if (status === 'authenticated') {
    return <>{children}</>;
  }

  // unauthenticated → navigate() will redirect to /login shortly
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-muted">
      <Spinner size="md" />
    </div>
  );
}