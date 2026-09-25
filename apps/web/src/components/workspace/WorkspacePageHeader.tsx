import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import type { WorkspacePage } from '@/lib/workspaces/registry';
import { workspacePageHref } from '@/lib/workspaces/registry';

/**
 * Workspace page header.
 *
 * The trail exposes the parent return path and the current location. A group
 * such as `operations` or `settings` is not itself a page, so no link is invented
 * for it: only real destinations appear in the ordered list.
 */
export async function WorkspacePageHeader({
  locale,
  page,
  children,
}: {
  locale: string;
  page: WorkspacePage;
  children?: React.ReactNode;
}) {
  const t = await getTranslations();
  const segments = page.path === '' ? [] : page.path.split('/');
  const parentPath = segments.slice(0, -1).join('/');
  const current = segments.at(-1) ?? '';

  return (
    <header>
      <nav aria-label={t('platformOverview.title')} className="text-xs">
        <ol className="flex flex-wrap items-center gap-2 text-ink-soft">
          <li>
            <Link href={workspacePageHref(locale, '')} className="hover:underline">
              {t('layout.mainNav')}
            </Link>
          </li>
          {parentPath !== '' ? (
            <>
              <li aria-hidden="true" className="text-ink-faint">
                /
              </li>
              <li>
                <Link href={workspacePageHref(locale, parentPath)} className="num hover:underline">
                  {`/${parentPath}`}
                </Link>
              </li>
            </>
          ) : null}
          {current !== '' ? (
            <>
              <li aria-hidden="true" className="text-ink-faint">
                /
              </li>
              <li aria-current="page" className="num font-semibold text-ink">
                {`/${current}`}
              </li>
            </>
          ) : null}
        </ol>
      </nav>

      <p className="num chip mt-4">{`/${locale}/workspace/${page.path}`}</p>
      <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">{t(page.labelKey)}</h1>
      <p className="mt-2 max-w-3xl text-sm text-ink-soft">{t(page.leadKey)}</p>
      {children}
    </header>
  );
}
