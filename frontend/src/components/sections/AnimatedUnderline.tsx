import { useRef } from 'react';
import { cn } from '../../lib/utils';

/** Text with animated gradient underline. */
export default function AnimatedUnderline({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  return (
    <span ref={ref} className={cn('relative inline-block', className)}>
      {children}
      <span
        className="absolute -bottom-1 left-0 h-0.5 bg-gradient-to-r from-[var(--color-leaf-400)] to-[var(--color-aqua-400)] transition-all duration-500"
        style={{ width: '100%' }}
        aria-hidden
      />
    </span>
  );
}
