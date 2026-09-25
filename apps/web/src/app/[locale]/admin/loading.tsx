import { getTranslations } from 'next-intl/server';

export default async function AdminLoading() {
  const t = await getTranslations('common');

  return (
    <div className="grid gap-8 lg:grid-cols-[17rem_minmax(0,1fr)]" aria-busy="true">
      <div className="hidden lg:block">
        <div className="h-7 w-32 animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-4 space-y-2">
          {Array.from({ length: 5 }, (_, index) => (
            <div
              // biome-ignore lint/suspicious/noArrayIndexKey: static placeholder rows
              key={index}
              className="h-12 animate-pulse rounded bg-[var(--color-surface-2)]"
            />
          ))}
        </div>
      </div>

      <div className="min-w-0" role="status" aria-label={t('pending')}>
        <div className="h-5 w-40 animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-4 h-9 w-64 animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-3 h-4 w-80 max-w-full animate-pulse rounded bg-[var(--color-surface-2)]" />
        <div className="mt-8 h-64 animate-pulse rounded bg-[var(--color-surface-2)]" />
      </div>
    </div>
  );
}
