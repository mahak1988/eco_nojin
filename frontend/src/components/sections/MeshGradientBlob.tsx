import { cn } from '../../lib/utils';

/** Decorative mesh gradient blob. */
export default function MeshGradientBlob({
  className,
  color = 'leaf',
}: {
  className?: string;
  color?: 'leaf' | 'aqua' | 'sand';
}) {
  const colors = {
    leaf: 'from-[var(--color-leaf-500)]/20 via-[var(--color-leaf-400)]/10 to-transparent',
    aqua: 'from-[var(--color-aqua-500)]/20 via-[var(--color-aqua-400)]/10 to-transparent',
    sand: 'from-[var(--color-sand-500)]/20 via-[var(--color-sand-400)]/10 to-transparent',
  };

  return (
    <div
      className={cn(
        'absolute rounded-full blur-3xl bg-gradient-to-br animate-float',
        colors[color],
        className
      )}
      aria-hidden
    />
  );
}
