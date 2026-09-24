"use client";

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface SwitchProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  checked?: boolean;
}

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className, checked, ...props }, ref) => {
    return (
      <button
        role="switch"
        aria-checked={checked}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          checked ? 'bg-forest' : 'bg-line',
          className
        )}
        ref={ref}
        {...props}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            checked ? 'translate-x-6' : 'translate-x-1'
          )}
          aria-hidden="true"
        />
      </button>
    );
  }
);
Switch.displayName = 'Switch';