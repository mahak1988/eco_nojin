import type { ReactNode } from 'react';
import { cn } from './cn';

export function ErrorState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div role="alert" className={cn('rounded-lg border border-clay/40 bg-clay/10 p-6', className)}>
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      {description && <p className="mt-2 text-sm text-ink-soft">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
