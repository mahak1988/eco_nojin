'use client';

type LocaleErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function LocaleError({ reset }: LocaleErrorProps) {
  return (
    <main className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold text-ink">Something went wrong</h1>
      <p className="text-ink-soft">The page could not be loaded. Please try again.</p>
      <button
        type="button"
        onClick={() => reset()}
        className="rounded-[var(--radius-8)] bg-[var(--color-forest)] px-4 py-2 font-semibold text-[var(--color-paper)]"
      >
        Try again
      </button>
    </main>
  );
}
