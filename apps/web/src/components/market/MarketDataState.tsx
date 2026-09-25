'use client';

import { useTranslations } from 'next-intl';
import type { ReactNode } from 'react';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import type { ApiFailureKind } from '@/lib/api/cart';

/**
 * The real data state of a marketplace surface. Nothing here invents content:
 * every message comes from the shipped catalogues and the optional `detail` is
 * the verbatim gateway error, so a failure is never dressed up as success.
 */
export type MarketDataState =
  | 'loading'
  | 'live'
  | 'empty'
  | 'unauthenticated'
  | 'unavailable'
  | 'error'
  | 'offline';

export interface MarketDataStateNoticeProps {
  state: MarketDataState;
  /** Verbatim gateway error text; only shown for the error state. */
  detail?: string;
  failureKind?: ApiFailureKind;
  locale: string;
  onRetry?: () => void;
  /** Localized empty-state copy owned by the page. */
  emptyMessage?: string;
  emptyAction?: ReactNode;
  loadingRows?: number;
}

export function MarketDataStateNotice({
  state,
  detail,
  failureKind,
  locale,
  onRetry,
  emptyMessage,
  emptyAction,
  loadingRows = 3,
}: MarketDataStateNoticeProps) {
  const common = useTranslations('common');
  const authCommon = useTranslations('auth.common');
  const authSession = useTranslations('auth.session');
  const statusLine = useTranslations('statusLine');
  const offline = useTranslations('offline');

  if (state === 'live') return null;

  if (state === 'loading') {
    return (
      <div role="status" aria-busy="true" aria-live="polite" data-market-state="loading">
        <Skeleton variant="card" lines={loadingRows} />
      </div>
    );
  }

  if (state === 'unauthenticated') {
    return (
      <div
        role="status"
        data-market-state="unauthenticated"
        className="rounded-[var(--radius-l)] border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4"
      >
        <p className="font-medium text-[var(--color-ink)]">{authSession('signedOut')}</p>
        <p className="mt-1 text-sm text-[var(--color-ink-soft)]">{authSession('signedOutLead')}</p>
        <a
          href={`/${locale}/auth/login`}
          className="mt-3 inline-flex rounded-[var(--radius-m)] border border-[var(--color-line)] px-3 py-2 text-sm font-semibold text-[var(--color-ink)]"
        >
          {authCommon('signIn')}
        </a>
      </div>
    );
  }

  if (state === 'offline') {
    return (
      <div
        role="status"
        data-market-state="offline"
        className="rounded-[var(--radius-l)] border border-[var(--color-copper)] bg-[var(--color-copper)]/10 p-4"
      >
        <p className="font-medium text-[var(--color-ink)]">{offline('title')}</p>
        <p className="mt-1 text-sm text-[var(--color-ink-soft)]">{offline('description')}</p>
        {onRetry ? (
          <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>
            {offline('retry')}
          </Button>
        ) : null}
      </div>
    );
  }

  if (state === 'unavailable') {
    return (
      <div
        role="status"
        data-market-state="unavailable"
        className="rounded-[var(--radius-l)] border border-[var(--color-line)] bg-[var(--color-surface-2)] p-4"
      >
        <p className="text-sm text-[var(--color-ink-soft)]">{statusLine('unavailable')}</p>
        {detail ? (
          <p className="mt-1 font-mono text-xs break-words text-[var(--color-ink-soft)]">
            {detail}
          </p>
        ) : null}
        {onRetry ? (
          <Button variant="ghost" size="sm" className="mt-3" onClick={onRetry}>
            {common('retry')}
          </Button>
        ) : null}
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div
        role="alert"
        data-market-state="error"
        data-failure-kind={failureKind ?? 'server'}
        className="rounded-[var(--radius-l)] border border-[var(--color-clay)] bg-[var(--color-clay)]/10 p-4"
      >
        <p className="font-medium text-[var(--color-ink)]">{common('error')}</p>
        {detail ? (
          <p className="mt-1 font-mono text-xs break-words text-[var(--color-ink-soft)]">
            {detail}
          </p>
        ) : null}
        {onRetry ? (
          <Button variant="ghost" size="sm" className="mt-3" onClick={onRetry}>
            {common('retry')}
          </Button>
        ) : null}
      </div>
    );
  }

  if (state === 'empty') {
    return (
      <div
        role="status"
        data-market-state="empty"
        className="rounded-[var(--radius-l)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 text-center"
      >
        {emptyMessage ? <p className="text-[var(--color-ink-soft)]">{emptyMessage}</p> : null}
        {emptyAction ? <div className="mt-4 flex justify-center">{emptyAction}</div> : null}
      </div>
    );
  }

  return null;
}
