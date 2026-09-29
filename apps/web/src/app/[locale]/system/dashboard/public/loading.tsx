export default function Loading() {
  return (
    <div
      className="mx-auto flex min-h-[50vh] max-w-5xl items-center justify-center px-6"
      aria-busy="true"
    >
      <div
        role="status"
        className="h-8 w-48 animate-pulse rounded bg-[var(--color-muted)]"
        aria-label="Loading"
      />
    </div>
  );
}
