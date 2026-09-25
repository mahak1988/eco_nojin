import { type ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from './cn';

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  size?: 'sm' | 'md' | 'lg';
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, size = 'md', className, type = 'button', ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      className={cn(
        'inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-line bg-surface text-ink transition-colors hover:bg-surface-2 focus-visible:ring-2 focus-visible:ring-focus disabled:pointer-events-none disabled:opacity-50',
        size === 'sm' && 'min-h-9 min-w-9',
        size === 'lg' && 'min-h-12 min-w-12',
        className,
      )}
      {...props}
    />
  ),
);

IconButton.displayName = 'IconButton';
