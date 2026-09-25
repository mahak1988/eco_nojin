import { cn } from './cn';

export function Spinner({ label = 'Loading', className }: { label?: string; className?: string }) {
  return (
    <span role="status" aria-label={label} className={cn('inline-flex', className)}>
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-line border-t-forest motion-reduce:animate-none"
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}
