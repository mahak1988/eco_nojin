import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from './cn';

const buttonVariants = cva(
  'inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-semibold transition-[color,box-shadow] outline-none focus-visible:ring-2 focus-visible:ring-primary/70 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow-sm hover:bg-primary/90',
        secondary: 'bg-secondary text-foreground shadow-sm ring-1 ring-border hover:bg-muted/20',
        outline: 'bg-transparent ring-1 ring-border hover:bg-muted/10',
        ghost: 'bg-transparent hover:bg-muted/10',
        destructive: 'bg-destructive text-white shadow-sm hover:bg-destructive/90',
      },
      size: {
        default: 'px-4 py-2',
        sm: 'min-h-9 px-3 text-xs',
        lg: 'min-h-12 px-6 text-base',
        icon: 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant, size, asChild = false, type = 'button', ...props },
    ref,
  ) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        type={asChild ? undefined : type}
        {...props}
      />
    );
  },
);

Button.displayName = 'Button';
export { buttonVariants };
