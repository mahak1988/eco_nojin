import { useEffect, useRef } from 'react';

/**
 * Focus trap hook for modal dialogs.
 * Traps focus within the container element when active.
 * Restores focus to the previously focused element on close.
 */
export function useFocusTrap(isActive: boolean, onDeactivate?: () => void) {
  const containerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isActive) return;

    const container = containerRef.current;
    if (!container) return;

    // Store the previously focused element
    previouslyFocusedRef.current = document.activeElement as HTMLElement;

    // Get all focusable elements
    const getFocusableElements = () =>
      container.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable]'
      );

    const focusableElements = getFocusableElements();
    const firstElement = focusableElements[0];

    // Focus the first element
    firstElement?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const focusable = getFocusableElements();
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      // Restore focus to previously focused element
      previouslyFocusedRef.current?.focus();
      onDeactivate?.();
    };
  }, [isActive, onDeactivate]);

  return containerRef;
}