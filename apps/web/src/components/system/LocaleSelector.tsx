'use client';

import { useId, useState } from 'react';
import { usePathname, useRouter } from '@/i18n/navigation';
import { type AppLocale, locales } from '@/i18n/routing';

const NATIVE_NAMES: Record<AppLocale, string> = {
  fa: 'فارسی',
  en: 'English',
  ar: 'العربية',
  ur: 'اردو',
  de: 'Deutsch',
  es: 'Español',
  fr: 'Français',
  hi: 'हिन्दी',
  it: 'Italiano',
  ms: 'Bahasa Melayu',
  pt: 'Português',
  ru: 'Русский',
  zh: '中文',
  bn: 'বাংলা',
};

export function LocaleSelector({
  current,
  label,
  actionLabel,
}: {
  current: string;
  label: string;
  actionLabel: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, setPending] = useState(current);
  const selectId = useId();
  const statusId = useId();
  const active = pending as AppLocale;
  const changed = pending !== current;

  return (
    <form
      className="mt-3 flex flex-wrap items-end gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (changed) router.replace(pathname, { locale: active });
      }}
    >
      <div>
        <label htmlFor={selectId} className="field-label block">
          {label}
        </label>
        <select
          id={selectId}
          name="locale"
          value={pending}
          onChange={(event) => setPending(event.target.value)}
          aria-describedby={statusId}
          className="mt-1 rounded-md border border-line bg-background px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-forest"
        >
          {locales.map((locale) => (
            <option key={locale} value={locale} lang={locale}>
              {NATIVE_NAMES[locale]} ({locale})
            </option>
          ))}
        </select>
      </div>
      <button type="submit" className="btn btn-ghost" disabled={!changed}>
        {actionLabel}
      </button>
      <p
        id={statusId}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="num pb-2 text-xs text-ink-soft"
      >
        {changed ? `${NATIVE_NAMES[active]} · ${active}` : ''}
      </p>
    </form>
  );
}
