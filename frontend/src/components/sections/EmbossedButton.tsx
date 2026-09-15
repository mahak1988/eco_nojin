import { cn } from '../../lib/utils';

/** 3D embossed button with press effect. */
export default function EmbossedButton({
  children,
  onClick,
  variant = 'primary',
  className,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
}) {
  const variants = {
    primary: 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]',
    secondary: 'bg-[var(--color-aqua-500)] text-[var(--color-night-950)]',
    ghost: 'glass text-[var(--color-night-100)]',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'embossed-btn rounded-2xl px-6 py-3 text-sm font-extrabold transition-all duration-200 hover:brightness-110 active:brightness-90',
        variants[variant],
        className
      )}
    >
      {children}
    </button>
  );
}
