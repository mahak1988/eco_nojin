import type { ReactNode } from 'react';
import { cn } from './cn';

export function Tag({
  children,
  tone = 'neutral',
  className,
}: {
  children: ReactNode;
  tone?: 'neutral' | 'positive' | 'warning' | 'critical';
  className?: string;
}) {
  const tones = {
    neutral: 'bg-surface-2 text-ink-soft',
    positive: 'bg-forest/10 text-forest',
    warning: 'bg-copper/10 text-copper',
    critical: 'bg-clay/10 text-clay',
  } as const;
  return (
    <span
      className={cn(
        'inline-flex min-h-7 items-center rounded-full px-3 text-xs font-medium',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
