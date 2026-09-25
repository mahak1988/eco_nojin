import type { ReactNode } from 'react';
import { cn } from './cn';

export function ChartFrame({
  title,
  description,
  children,
  source,
  className,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  source?: string;
  className?: string;
}) {
  return (
    <figure className={cn('rounded-lg border border-line bg-surface p-4', className)}>
      <figcaption className="mb-3">
        <h3 className="font-semibold text-ink">{title}</h3>
        {description && <p className="mt-1 text-sm text-ink-soft">{description}</p>}
        {source && <p className="mt-1 text-xs text-ink-faint">{source}</p>}
      </figcaption>
      {children}
    </figure>
  );
}
