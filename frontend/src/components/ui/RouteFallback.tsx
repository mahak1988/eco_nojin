/** Full-page loading state used as the lazy-route Suspense fallback. */
export default function RouteFallback() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center" role="status" aria-live="polite">
      <div className="flex flex-col items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-leaf-500/25 border-t-leaf-400" />
        <span className="text-sm text-emerald-100/50">Eco Nojin</span>
      </div>
    </div>
  );
}
