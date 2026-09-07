import { useEffect, useRef, type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type FocusTrapProps = {
  children: ReactNode;
  className?: string;
  active?: boolean;
};

export function FocusTrap({ children, className, active = true }: FocusTrapProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active || !rootRef.current) return;

    const root = rootRef.current;
    const focusableSelector = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const focusableElements = () =>
      Array.from(root.querySelectorAll<HTMLElement>(focusableSelector)).filter((el) => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
      });

    const first = () => focusableElements()[0];
    const last = () => focusableElements().at(-1) ?? focusableElements()[0];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const elements = focusableElements();
      if (elements.length === 0) {
        e.preventDefault();
        return;
      }

      const current = document.activeElement as HTMLElement | null;
      const currentIndex = current ? elements.indexOf(current) : -1;

      if (e.shiftKey) {
        if (currentIndex <= 0) {
          e.preventDefault();
          last()?.focus();
        }
      } else {
        if (currentIndex >= elements.length - 1) {
          e.preventDefault();
          first()?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [active]);

  return (
    <div ref={rootRef} className={cn('relative', className)}>
      {children}
    </div>
  );
}
