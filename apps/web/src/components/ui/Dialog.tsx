"use client";

import React, {
  type ReactNode,
  useEffect,
  useRef,
  useCallback,
  forwardRef,
  type HTMLAttributes,
  type CSSProperties,
} from "react";
import { createPortal } from "react-dom";

export interface DialogProps extends Omit<HTMLAttributes<HTMLDialogElement>, "open"> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  portalTarget?: HTMLElement | null;
}

const overlayStyles: CSSProperties = {
  position: "fixed",
  inset: 0,
  backgroundColor: "color-mix(in oklch, var(--color-ink) 60%, transparent)",
  backdropFilter: "blur(4px)",
  WebkitBackdropFilter: "blur(4px)",
  zIndex: 99,
  animation: "fadeIn var(--duration-120) var(--easing-ease-out-quart)",
};

const dialogStyles: CSSProperties = {
  position: "fixed",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  maxWidth: "calc(100vw - var(--space-8))",
  maxHeight: "calc(100vh - var(--space-8))",
  width: "min(560px, 100%)",
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-line)",
  borderRadius: "var(--radius-16)",
  boxShadow: "var(--shadow-pop)",
  padding: "var(--space-6)",
  zIndex: 100,
  overflow: "auto",
  animation: "slideUp var(--duration-240) var(--easing-ease-out-quart)",
};

const keyframes = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translate(-50%, -48%); }
    to { opacity: 1; transform: translate(-50%, -50%); }
  }
`;

const cancelButtonStyles: CSSProperties = {
  padding: "var(--space-2) var(--space-4)",
  fontFamily: "var(--font-sans)",
  fontSize: "0.875rem",
  fontWeight: 600,
  borderRadius: "var(--radius-8)",
  border: "1px solid var(--color-line)",
  background: "var(--color-surface)",
  color: "var(--color-ink)",
  cursor: "pointer",
  transition: "background-color var(--duration-120) var(--easing-ease-out-quart)",
};

export const Dialog = forwardRef<HTMLDialogElement, DialogProps>(
  ({ open, onOpenChange, title, description, children, portalTarget, className = "", style, ...props }, ref) => {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const previousActiveElement = useRef<HTMLElement | null>(null);
    const focusableElementsRef = useRef<HTMLElement[]>([]);

    const handleKeyDown = useCallback(
      (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          event.preventDefault();
          onOpenChange(false);
        }

        if (event.key === "Tab") {
          const focusableElements = focusableElementsRef.current;
          if (focusableElements.length === 0) return;

          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (event.shiftKey && document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          } else if (!event.shiftKey && document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      },
      [onOpenChange]
    );

    useEffect(() => {
      if (open) {
        previousActiveElement.current = document.activeElement as HTMLElement;
        document.addEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "hidden";

        const dialog = dialogRef.current;
        if (dialog) {
          const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
          focusableElementsRef.current = Array.from(dialog.querySelectorAll<HTMLElement>(focusableSelector));
          const firstFocusable = focusableElementsRef.current[0];
          if (firstFocusable) firstFocusable.focus();
        }
      } else {
        document.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "";
        previousActiveElement.current?.focus();
      }

      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "";
      };
    }, [open, handleKeyDown]);

    const content = (
      <>
        <style dangerouslySetInnerHTML={{ __html: keyframes }} />
        <div
          style={overlayStyles}
          onClick={() => onOpenChange(false)}
          aria-hidden="true"
        />
        <dialog
          ref={dialogRef}
          open={open}
          style={{
            ...style,
            ...dialogStyles,
          }}
          className={className}
          onClick={(e) => e.stopPropagation()}
          {...props}
        >
          <header style={{ marginBottom: "var(--space-4)" }}>
            <h2 id="dialog-title" style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", fontWeight: "600", color: "var(--color-ink)", margin: 0 }}>
              {title}
            </h2>
            {description && (
              <p id="dialog-description" style={{ fontFamily: "var(--font-sans)", fontSize: "0.875rem", color: "var(--color-ink-soft)", margin: "var(--space-2) 0 0 0" }}>
                {description}
              </p>
            )}
          </header>
          <div style={{ marginBottom: "var(--space-6)" }}>{children}</div>
          <footer style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-3)" }}>
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              style={cancelButtonStyles}
            >
              Cancel
            </button>
          </footer>
        </dialog>
      </>
    );

    if (!open) return null;

    const target = portalTarget ?? document.body;
    return createPortal(content, target);
  }
);

Dialog.displayName = "Dialog";

export default Dialog;