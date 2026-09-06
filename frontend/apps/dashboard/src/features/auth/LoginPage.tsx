import { useId, useRef, useState, type FormEvent } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuth } from '@eco/auth';
import { Alert, Button, Card, CardBody, Input, Spinner } from '@eco/ui';

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactElement<{ id: string; 'aria-describedby'?: string; 'aria-invalid'?: boolean }>;
}) {
  return (
    <div className="flex flex-col gap-1 text-xs text-ink-muted">
      <span className="font-medium text-ink">{label}</span>
      {children}
      {error && (
        <span role="alert" className="text-danger">
          {error}
        </span>
      )}
    </div>
  );
}

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const auth = useAuth();
  const navigate = useNavigate();

  const emailId = useId();
  const passwordId = useId();
  const errorId = useId();
  const emailRef = useRef<HTMLInputElement>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === 'signin') {
        await auth.signIn(email, password);
      } else {
        await auth.signUp(email, password);
      }
      void navigate({ to: '/' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main
      role="main"
      aria-label="صفحهٔ ورود"
      className="flex min-h-screen items-center justify-center bg-surface-muted p-4"
    >
      <Card className="w-full max-w-md">
        <CardBody>
          <div className="mb-6 text-center">
            <div
              aria-hidden="true"
              className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-lg bg-brand-600 text-lg font-bold text-white"
            >
              EN
            </div>
            <h1 className="text-2xl font-semibold">HyDroMa — Sign in</h1>
            <p className="mt-1 text-sm text-ink-muted">
              {auth.isSupabaseConfigured
                ? 'Supabase authentication is enabled.'
                : 'Supabase is not configured. You can sign in via the dev fallback below.'}
            </p>
          </div>

          <div
            id={errorId}
            role={error ? 'alert' : undefined}
            aria-live="polite"
            className="mb-2"
          >
            {error && (
              <Alert tone="danger" title="Authentication failed" className="mb-2">
                {error}
              </Alert>
            )}
          </div>

          {auth.status === 'loading' && !submitting && (
            <div className="mb-3 flex items-center gap-2 text-sm text-ink-muted">
              <Spinner size="sm" aria-hidden={false} aria-label="Loading session" />
              <span>Restoring session…</span>
            </div>
          )}

          <form onSubmit={submit} className="flex flex-col gap-3" noValidate={false}>
            <Field label="Email">
              <Input
                id={emailId}
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail((e.target as HTMLInputElement).value)}
                required
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? errorId : undefined}
                ref={emailRef}
              />
            </Field>
            <Field label="Password">
              <Input
                id={passwordId}
                type="password"
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword((e.target as HTMLInputElement).value)}
                required
                minLength={6}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? errorId : undefined}
              />
            </Field>
            <Button
              type="submit"
              disabled={submitting || !email || !password}
              aria-label={mode === 'signin' ? 'ورود به سیستم' : 'ایجاد حساب کاربری'}
            >
              {submitting && <Spinner size="sm" tone="inverse" />}
              {mode === 'signin' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <div className="mt-4 flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={() => setMode((m) => (m === 'signin' ? 'signup' : 'signin'))}
              className="text-brand-700 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
              aria-pressed={mode === 'signup'}
            >
              {mode === 'signin' ? 'Need an account? Sign up' : 'Have an account? Sign in'}
            </button>
            {!auth.isSupabaseConfigured && (
              <button
                type="button"
                onClick={() => {
                  auth.devSignIn({ email: email || 'demo@eco-nojin.local' });
                  void navigate({ to: '/' });
                }}
                className="text-ink-muted hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
              >
                Continue as demo user
              </button>
            )}
          </div>
        </CardBody>
      </Card>
    </main>
  );
}