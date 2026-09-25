import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import { type AdminSection, adminSectionHref } from './admin-sections';

/**
 * Console page header.
 *
 * The trail is an ordered list of real destinations only — the console index
 * and the current section. Intermediate groups such as `system` or
 * `localization` are not pages, so no link is invented for them.
 */
export async function AdminPageHeader({
  locale,
  section,
  children,
}: {
  locale: string;
  section: AdminSection;
  children?: React.ReactNode;
}) {
  const t = await getTranslations();
  const isIndex = section.path === '';

  return (
    <header>
      <nav aria-label={t('platformOverview.title')} className="text-xs">
        <ol className="flex flex-wrap items-center gap-2 text-ink-soft">
          <li>
            {isIndex ? (
              <span aria-current="page" className="font-semibold text-ink">
                {t(section.labelKey)}
              </span>
            ) : (
              <Link href={adminSectionHref(locale, '')} className="hover:underline">
                {t('statusPage.title')}
              </Link>
            )}
          </li>
          {!isIndex ? (
            <li aria-hidden="true" className="text-ink-faint">
              /
            </li>
          ) : null}
          {!isIndex ? (
            <li aria-current="page" className="num font-semibold text-ink">
              {`/${section.path}`}
            </li>
          ) : null}
        </ol>
      </nav>

      <p className="num chip mt-4">{`/${locale}/admin/${section.path}`}</p>
      <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">
        {t(section.labelKey)}
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-ink-soft">{t(section.leadKey)}</p>
      {children}
    </header>
  );
}
