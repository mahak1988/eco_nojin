'use client';

import { useEffect } from 'react';
import { copyFor, directionFor, localeFromPath } from '@/lib/error-copy';

/**
 * Segment error boundary.
 *
 * The previous revision rendered three hard-coded English strings, which
 * `I18N_AND_RTL.md` forbids for visible text and which left a Persian or Arabic
 * reader with an English-only failure page at the worst possible moment. The copy
 * now comes from `lib/error-copy`, the same provider-free source
 * `app/global-error.tsx` uses, so both boundaries behave identically.
 */
export default function LocaleError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const locale = localeFromPath(typeof window === 'undefined' ? '' : window.location.pathname);
  const copy = copyFor(locale, 'segment');
  const dir = directionFor(locale);

  useEffect(() => {
    // The message is logged rather than rendered: the digest is the only handle a
    // reader can quote, and it must not be the thing that leaks to a third party.
    console.error('route error', { digest: error.digest, locale });
  }, [error.digest, locale]);

  return (
    <main
      id="main"
      dir={dir}
      className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center"
    >
      <h1 className="text-2xl font-semibold text-ink">{copy.title}</h1>
      <p className="text-ink-soft">{copy.description}</p>
      <p className="text-xs text-ink-faint">{copy.reference}</p>
      {error.digest ? <p className="num text-xs text-ink-faint">{error.digest}</p> : null}
      <button
        type="button"
        onClick={() => reset()}
        className="rounded-[var(--radius-8)] bg-[var(--color-action)] px-4 py-2 font-semibold text-[var(--color-on-action)]"
      >
        {copy.retry}
      </button>
    </main>
  );
}
