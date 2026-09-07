import { type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type BrandPatternProps = {
  children?: ReactNode;
  className?: string;
  color?: string;
  opacity?: number;
};

export function BrandPattern({
  children,
  className,
  color = 'rgb(22 163 74 / 0.05)',
  opacity = 0.05,
}: BrandPatternProps) {
  return (
    <div
      className={cn('absolute inset-0 overflow-hidden', className)}
      aria-hidden="true"
      style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, ${color} 1px, transparent 0)`,
        backgroundSize: '24px 24px',
        opacity,
      }}
    >
      {children}
    </div>
  );
}
