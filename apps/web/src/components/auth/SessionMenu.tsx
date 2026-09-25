'use client';

import { useEffect, useId, useRef, useState } from 'react';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Link } from '@/i18n/navigation';
import { AuthErrorAlert } from './AuthErrorAlert';
import { type AuthErrorKey, errorDetail, toAuthErrorKey } from './errors';
import { roleLabelKey } from './role-label';
import { useAuthMessage } from './useAuthMessage';

/**
 * Session control for the site navigation: a sign-in entry point while signed
 * out, and a disclosure with the session details link and sign-out while
 * signed in. All copy comes from the `auth` namespace.
 */
export function SessionMenu() {
  const t = useAuthMessage();
  const { user, loading, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [failure, setFailure] = useState<{ messageKey: AuthErrorKey; detail?: string } | null>(
    null,
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setOpen(false);
      toggleRef.current?.focus();
    };
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (loading) {
    return (
      <span role="status" aria-busy="true" className="text-sm text-ink-soft">
        {t('auth.common.checkingSession')}
      </span>
    );
  }

  if (!user) {
    return (
      <Link
        href="/auth/login"
        className="btn btn-ghost text-sm"
        aria-label={t('auth.common.signInLabel')}
      >
        {t('auth.common.signIn')}
      </Link>
    );
  }

  const displayName = user.full_name?.trim() || user.email;
  const roleKey = roleLabelKey(user.role);

  async function handleSignOut() {
    setSigningOut(true);
    setFailure(null);
    try {
      await logout();
      setOpen(false);
    } catch (error) {
      setFailure({
        messageKey: toAuthErrorKey(error, 'auth.errors.signOutFailed'),
        detail: errorDetail(error),
      });
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={toggleRef}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex max-w-[12rem] items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1.5 text-sm text-[var(--ink)] transition-colors hover:border-[var(--forest)] hover:bg-[var(--surface-2)]"
      >
        <span className="sr-only">{t('auth.common.signedInAs')}: </span>
        <span className="max-w-[9rem] truncate">{displayName}</span>
      </button>

      <section
        id={panelId}
        hidden={!open}
        aria-label={t('auth.common.accountMenu')}
        className="absolute end-0 z-50 mt-2 w-72 rounded-[var(--radius-l)] border border-[var(--line)] bg-[var(--surface)] p-3 text-start shadow-[var(--shadow-pop)]"
      >
        <p className="text-[11px] font-semibold tracking-wide text-[var(--ink-soft)] uppercase">
          {t('auth.common.signedInAs')}
        </p>
        <p className="mt-1 truncate text-sm text-[var(--ink)]" dir="auto">
          {displayName}
        </p>
        <p className="truncate text-xs text-[var(--ink-soft)]" dir="auto">
          {user.email}
        </p>
        {roleKey ? <p className="mt-1 text-xs text-[var(--ink-soft)]">{t(roleKey)}</p> : null}

        <Link
          href="/account/session"
          onClick={() => setOpen(false)}
          className="mt-3 block text-sm text-[var(--water)] hover:underline"
        >
          {t('auth.common.sessionDetails')}
        </Link>

        <Button
          variant="secondary"
          size="sm"
          loading={signingOut}
          onClick={handleSignOut}
          className="mt-3 w-full"
        >
          {signingOut ? t('auth.common.signingOut') : t('auth.common.signOut')}
        </Button>

        {failure ? (
          <div className="mt-3">
            <AuthErrorAlert messageKey={failure.messageKey} detail={failure.detail} />
          </div>
        ) : null}
      </section>
    </div>
  );
}
