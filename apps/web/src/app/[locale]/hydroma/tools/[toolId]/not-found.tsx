import Link from 'next/link';
import { getTranslations } from 'next-intl/server';

/**
 * Reached when a tool id is neither in the declared catalogue nor resolvable to
 * an execution contract.
 *
 * The message says which of the two it is, because the two mean different
 * things to whoever has to fix it: an id that was never declared is a typo, and
 * a declared id with no route is a missing gateway contract. Reporting a 404
 * for both would hide the second.
 */
export default async function ToolNotFound() {
  const t = await getTranslations('tools');

  return (
    <main id="main" className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 pb-16 sm:px-6">
      <div data-region="title" className="flex flex-col gap-3">
        <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">
          {t('notFound.title')}
        </h1>
        <p className="max-w-2xl text-sm text-pretty text-ink-soft">{t('notFound.description')}</p>
        <p className="max-w-2xl text-sm text-pretty text-ink-soft">{t('notFound.detail')}</p>
      </div>
      <div data-region="actions" className="flex flex-wrap items-center gap-3">
        <Link href="../" className="btn btn-ghost">
          {t('actions.back')}
        </Link>
      </div>
    </main>
  );
}
