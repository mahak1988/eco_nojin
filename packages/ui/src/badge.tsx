import { cva, type VariantProps } from 'class-variance-authority';
import type { HTMLAttributes, ForwardedRef } from 'react';
import { forwardRef } from 'react';
import { cn } from './cn';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-primary/60',
  {
    variants: {
      variant: {
        default: 'bg-primary/15 text-primary',
        secondary: 'bg-muted text-muted-foreground',
        success: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
        warning: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
        destructive: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
        outline: 'text-foreground ring-1 ring-border',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant, className }))} {...props} />
  ),
);
Badge.displayName = 'Badge';

export { badgeVariants };
