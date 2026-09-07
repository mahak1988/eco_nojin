import { type ReactNode, useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Button } from '../primitives';

export type FloatingToolbarProps = {
  children: ReactNode;
  className?: string;
  offset?: number;
  showOnScrollUp?: boolean;
};

export function FloatingToolbar({
  children,
  className,
  offset = 60,
  showOnScrollUp = true,
}: FloatingToolbarProps) {
  const [isVisible, setIsVisible] = useState(false);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      if (showOnScrollUp) {
        setIsVisible(currentScrollY > lastScrollY.current + offset);
      } else {
        setIsVisible(currentScrollY > offset);
      }
      lastScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [offset, showOnScrollUp]);

  return (
    <div
      className={cn(
        'fixed bottom-4 inset-x-0 z-30 flex justify-center transition-transform duration-300 ease-out-soft',
        isVisible ? 'translate-y-0' : 'translate-y-full',
        className,
      )}
    >
      <div className="flex items-center gap-2 rounded-full border border-ink/10 bg-surface/90 px-2 py-2 shadow-raised backdrop-blur-xl">
        {children}
      </div>
    </div>
  );
}

export type FloatingToolbarButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  active?: boolean;
  className?: string;
};

export function FloatingToolbarButton({
  children,
  onClick,
  active = false,
  className,
}: FloatingToolbarButtonProps) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className={cn(
        'rounded-full',
        active && 'bg-surface-muted text-brand-700',
        className,
      )}
    >
      {children}
    </Button>
  );
}
