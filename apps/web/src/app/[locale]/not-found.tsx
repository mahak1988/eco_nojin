import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[50vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold text-ink">Page not found</h1>
      <Link href="/" className="font-semibold text-[var(--color-forest)]">
        Return home
      </Link>
    </main>
  );
}
