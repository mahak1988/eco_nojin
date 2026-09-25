import { cn } from './cn';

export interface ProgressProps {
  value: number;
  max?: number;
  label: string;
  className?: string;
}

export function Progress({ value, max = 100, label, className }: ProgressProps) {
  const safeValue = Math.min(Math.max(value, 0), max);
  return (
    <div className={cn('w-full', className)}>
      <div className="mb-1 flex justify-between text-xs text-ink-soft">
        <span>{label}</span>
        <span className="num">{Math.round((safeValue / max) * 100)}%</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={safeValue}
        className="h-2 overflow-hidden rounded-full bg-surface-2"
      >
        <div
          className="h-full rounded-full bg-forest transition-[inline-size] duration-240"
          style={{ inlineSize: `${(safeValue / max) * 100}%` }}
        />
      </div>
    </div>
  );
}
