import { cn } from '../../lib/utils';

/** Holographic iridescent badge. */
export default function HolographicBadge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'holographic-border inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold',
        'bg-[var(--color-night-800)] text-[var(--color-leaf-300)]',
        className
      )}
    >
      {children}
    </span>
  );
}
