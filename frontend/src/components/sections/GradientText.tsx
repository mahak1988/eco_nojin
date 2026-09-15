import { cn } from '../../lib/utils';

/** Animated gradient text heading. */
export default function GradientText({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'bg-gradient-to-r from-[var(--color-leaf-300)] via-[var(--color-aqua-400)] to-[var(--color-sand-400)] bg-[length:200%] bg-clip-text text-transparent animate-[shimmer_4s_linear_infinite]',
        className
      )}
    >
      {children}
    </span>
  );
}
