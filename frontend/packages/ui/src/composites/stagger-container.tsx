import { type ReactNode, useMemo } from 'react';
import { cn } from '@eco/utils';

export type StaggerContainerProps = {
  children: ReactNode;
  staggerDelay?: number;
  className?: string;
  as?: 'div' | 'ul' | 'ol';
};

export function StaggerContainer({
  children,
  staggerDelay = 70,
  className,
  as = 'div',
}: StaggerContainerProps) {
  const childArray = useMemo(() => {
    const arr = Array.isArray(children) ? children : [children];
    return arr.map((child, i) => (
      <div
        key={i}
        className={cn('animate-in-up')}
        style={{ animationDelay: `${i * staggerDelay}ms`, animationFillMode: 'both' }}
      >
        {child}
      </div>
    ));
  }, [children, staggerDelay]);

  const Component = as;
  return <Component className={cn('flex flex-col', className)}>{childArray}</Component>;
}
