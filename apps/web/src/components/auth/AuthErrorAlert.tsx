'use client';

import { type AuthErrorKey } from './errors';
import { useAuthMessage } from './useAuthMessage';

export interface AuthErrorAlertProps {
  messageKey: AuthErrorKey;
  detail?: string;
}

/**
 * Failure notice for a rejected auth request. The message is always a message
 * key; the raw server detail is rendered as locale-neutral supplementary text.
 */
export function AuthErrorAlert({ messageKey, detail }: AuthErrorAlertProps) {
  const t = useAuthMessage();

  return (
    <div
      role="alert"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-4 text-start"
    >
      <p className="text-sm font-semibold text-[var(--copper)]">{t('auth.common.errorHeading')}</p>
      <p className="mt-1 text-sm text-ink">{t(messageKey)}</p>
      {detail ? (
        <p className="mt-2 text-xs text-ink-soft" dir="auto">
          <span className="font-semibold">{t('auth.common.errorDetails')}: </span>
          {detail}
        </p>
      ) : null}
    </div>
  );
}
