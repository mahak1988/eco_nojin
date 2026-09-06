import { cn } from '@eco/utils';

export function TopBar() {
  return (
    <header className={cn('border-b border-ink/10 bg-surface px-6 py-4 flex items-center justify-between')}>
      <div>
        <h2 className={cn('text-lg font-semibold text-brand-700')}>Dashboard</h2>
      </div>
      <div className="flex items-center gap-4">
        <button
          type="button"
          className={cn(
            'px-4 py-2 rounded-lg text-white transition-colors hover:opacity-90',
            'bg-brand-600 hover:bg-brand-700',
          )}
        >
          New Analysis
        </button>
        <div className="h-8 w-8 rounded-full bg-surface-muted flex items-center justify-center text-ink-muted">
          👤
        </div>
      </div>
    </header>
  );
}