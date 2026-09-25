import { getTranslations } from 'next-intl/server';

export default async function AdminLoading() {
  const t = await getTranslations('common');

  return (
    <div className="mx-auto max-w-6xl px-6 py-12" aria-busy="true">
      <div role="status" aria-label={t('pending')}>
        <div className="h-8 w-56 animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-4 h-4 w-80 max-w-full animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="card h-40 animate-pulse bg-[var(--color-surface-2)]" />
          <div className="card h-40 animate-pulse bg-[var(--color-surface-2)]" />
        </div>
        <div className="card mt-4 h-24 animate-pulse bg-[var(--color-surface-2)]" />
      </div>
    </div>
  );
}
