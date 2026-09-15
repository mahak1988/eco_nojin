import { cn } from '../../lib/utils';

/** Floating 3D decorative shape. */
export default function FloatingShape({
  shape = 'circle',
  size = 80,
  color = 'leaf',
  className,
  delay = 0,
}: {
  shape?: 'circle' | 'ring' | 'blob';
  size?: number;
  color?: 'leaf' | 'aqua' | 'sand';
  className?: string;
  delay?: number;
}) {
  const colors = {
    leaf: 'bg-[var(--color-leaf-500)]/10 border-[var(--color-leaf-500)]/20',
    aqua: 'bg-[var(--color-aqua-500)]/10 border-[var(--color-aqua-500)]/20',
    sand: 'bg-[var(--color-sand-500)]/10 border-[var(--color-sand-500)]/20',
  };

  const isRing = shape === 'ring';

  return (
    <div
      className={cn(
        'maglev-item absolute pointer-events-none',
        isRing
          ? `rounded-full border-2 ${colors[color]}`
          : shape === 'blob'
            ? `rounded-[40%_60%_60%_40%/60%_30%_70%_40%] ${colors[color]}`
            : `rounded-full ${colors[color]}`,
        className
      )}
      style={{
        width: size,
        height: size,
        animationDelay: `${delay}s`,
      }}
      aria-hidden
    />
  );
}
