import type { ForwardedRef, LabelHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from './cn';

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn('text-sm font-medium text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-50', className)}
      {...props}
    />
  ),
);
Label.displayName = 'Label';
