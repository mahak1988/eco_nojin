'use client';

import { useTranslations } from 'next-intl';

type AdminErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function AdminError({ error, reset }: AdminErrorProps) {
  const t = useTranslations();

  return (
    <div className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-start gap-4 px-6 py-12">
      <h1 className="display text-3xl font-bold text-ink">{t('common.error')}</h1>
      <p className="text-sm text-ink-soft">{t('auth.errors.unknown')}</p>
      {error.digest ? <p className="num text-xs text-ink-faint">{error.digest}</p> : null}
      <button type="button" onClick={() => reset()} className="btn btn-ghost">
        {t('common.retry')}
      </button>
    </div>
  );
}
