'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { ADMIN_SECTIONS, adminSectionHref } from './admin-sections';

/**
 * Console side navigation. The active entry is marked with `aria-current="page"`
 * so assistive technology and keyboard users always know where they are, and
 * every entry also exposes its locale-neutral route so the section stays
 * identifiable even where the heading is reused from the shared vocabulary.
 */
export function AdminNav() {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations();

  return (
    <nav aria-label={t('layout.mainNav')} className="lg:sticky lg:top-6 lg:self-start">
      <p className="num chip">/{locale}/admin</p>
      <ul className="mt-3 flex flex-wrap gap-2 lg:flex-col">
        {ADMIN_SECTIONS.map((section) => {
          const href = adminSectionHref(locale, section.path);
          const current = pathname === href;
          return (
            <li key={section.id}>
              <Link
                href={href}
                aria-current={current ? 'page' : undefined}
                className={`flex min-h-11 w-full flex-col justify-center rounded-[var(--radius-m)] border px-3 py-2 transition-micro ${
                  current
                    ? 'border-[var(--canopy)] bg-[var(--surface-2)]'
                    : 'border-[var(--line)] bg-[var(--surface)] hover:bg-[var(--surface-2)]'
                }`}
              >
                <span
                  className={`text-sm font-semibold ${current ? 'text-[var(--ink)]' : 'text-[var(--ink-soft)]'}`}
                >
                  {t(section.labelKey)}
                </span>
                <span className="num text-[0.65rem] text-[var(--ink-faint)]">
                  {section.path === '' ? '/' : `/${section.path}`}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
