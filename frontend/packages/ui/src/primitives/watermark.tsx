import { type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type WatermarkProps = {
  children?: ReactNode;
  text?: string;
  className?: string;
  opacity?: number;
  fontSize?: number;
};

export function Watermark({
  children,
  text = 'Eco Nojin',
  className,
  opacity = 0.05,
  fontSize = 24,
}: WatermarkProps) {
  return (
    <div
      className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}
      aria-hidden="true"
    >
      <div
        className="whitespace-nowrap select-none"
        style={{
          opacity,
          fontSize,
          transform: 'rotate(-30deg)',
          transformOrigin: 'center',
        }}
      >
        {children ?? (
          <div className="flex flex-wrap gap-8">
            {Array.from({ length: 20 }).map((_, i) => (
              <span key={i} className="text-ink">
                {text}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
