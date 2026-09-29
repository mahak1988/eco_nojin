'use client';

/**
 * The last-resort boundary.
 *
 * Next.js replaces the whole root layout when this renders, so there is no
 * message provider, no session context and no shared component tree. The page
 * therefore styles itself with the design tokens inlined and reads its text from
 * `lib/error-copy`, which resolves the locale from the URL. Nothing here may
 * import from `next-intl`: the provider it would need is exactly what this
 * boundary destroys.
 */
import { copyFor, directionFor, localeFromPath } from '@/lib/error-copy';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const locale = localeFromPath(typeof window === 'undefined' ? '' : window.location.pathname);
  const copy = copyFor(locale, 'global');
  const dir = directionFor(locale);

  return (
    <html lang={locale ?? 'en'} dir={dir}>
      <body
        style={{
          margin: 0,
          minHeight: '100dvh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--color-paper)',
          color: 'var(--color-ink)',
          fontFamily: 'var(--font-sans)',
        }}
      >
        <main
          style={{
            maxWidth: '32rem',
            padding: '2rem 1.5rem',
            textAlign: dir === 'rtl' ? 'right' : 'left',
          }}
        >
          <h1 style={{ fontSize: '1.5rem', margin: '0 0 0.75rem' }}>{copy.title}</h1>
          <p style={{ margin: '0 0 1.5rem', lineHeight: 1.6, opacity: 0.8 }}>{copy.description}</p>
          <p style={{ margin: '0 0 1.5rem', fontSize: '0.8125rem', opacity: 0.7 }}>
            {copy.reference}
          </p>
          {error.digest ? (
            <p
              style={{
                margin: '0 0 1.5rem',
                fontSize: '0.75rem',
                opacity: 0.6,
                wordBreak: 'break-all',
              }}
            >
              {error.digest}
            </p>
          ) : null}
          <button
            type="button"
            onClick={() => reset()}
            style={{
              border: '1px solid var(--color-action)',
              background: 'var(--color-action)',
              color: 'var(--color-on-action)',
              borderRadius: 'var(--radius-8)',
              padding: '0.5rem 1rem',
              font: 'inherit',
              cursor: 'pointer',
            }}
          >
            {copy.retry}
          </button>
        </main>
      </body>
    </html>
  );
}
