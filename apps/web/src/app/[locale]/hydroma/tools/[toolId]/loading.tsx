import { getTranslations } from 'next-intl/server';

import { Skeleton } from '@/components/ui/Skeleton';

/**
 * The streaming state of §4.5, for the contract fetch and the first run.
 *
 * A shape that mirrors the instrument — contract at the inline start, result
 * beside it, provenance bar underneath — so the page does not jump when the real
 * surface arrives. No copy is invented: the accessible name comes from the
 * `tools` namespace, like every other string on the route.
 */
export default async function ToolLoading() {
  const t = await getTranslations('tools');

  return (
    <main
      id="main"
      data-page-template="T07"
      className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 pb-16 sm:px-6"
    >
      <header data-region="title" className="flex flex-col gap-3">
        <Skeleton variant="text" width="12rem" />
        <Skeleton variant="text" width="60%" height="2rem" />
      </header>
      <p role="status" aria-live="polite" className="text-sm text-ink-soft">
        {t('states.loading')}
      </p>
      <div className="grid gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]">
        <div data-region="instrument-input" className="min-w-0">
          <Skeleton variant="card" lines={6} />
        </div>
        <div data-region="instrument-output" className="min-w-0">
          <Skeleton variant="card" lines={8} />
        </div>
      </div>
      <div data-region="summary" className="min-w-0">
        <Skeleton variant="card" lines={2} />
      </div>
    </main>
  );
}
