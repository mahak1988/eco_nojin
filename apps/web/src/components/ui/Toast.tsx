"use client";

import React, { useEffect, useState, type ReactNode, forwardRef, type HTMLAttributes, type CSSProperties } from "react";

export type ToastVariant = "info" | "success" | "warning" | "error";

export interface ToastProps extends HTMLAttributes<HTMLDivElement> {
  variant?: ToastVariant;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  duration?: number;
  onClose?: () => void;
}

const variantStyles: Record<ToastVariant, { bg: string; border: string; icon: string }> = {
  info: {
    bg: "var(--color-surface)",
    border: "var(--color-water)",
    icon: "ℹ️",
  },
  success: {
    bg: "var(--color-surface)",
    border: "var(--color-forest)",
    icon: "✓",
  },
  warning: {
    bg: "var(--color-surface)",
    border: "var(--color-copper)",
    icon: "⚠",
  },
  error: {
    bg: "var(--color-surface)",
    border: "var(--color-clay)",
    icon: "✕",
  },
};

const baseStyles: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  gap: "var(--space-3)",
  padding: "var(--space-4)",
  borderRadius: "var(--radius-12)",
  borderLeft: "4px solid",
  boxShadow: "var(--shadow-pop)",
  minWidth: "320px",
  maxWidth: "480px",
  animation: "slideIn var(--duration-240) var(--easing-ease-out-quart)",
};

const keyframes = `
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(100%); }
    to { opacity: 1; transform: translateX(0); }
  }
  @keyframes slideOut {
    from { opacity: 1; transform: translateX(0); }
    to { opacity: 0; transform: translateX(100%); }
  }
`;

const closeButtonStyles: CSSProperties = {
  flexShrink: 0,
  padding: "var(--space-1)",
  background: "transparent",
  border: "none",
  color: "var(--color-ink-faint)",
  cursor: "pointer",
  borderRadius: "var(--radius-2)",
  transition: "color var(--duration-120) var(--easing-ease-out-quart)",
};

export const Toast = forwardRef<HTMLDivElement, ToastProps>(
  ({ variant = "info", title, description, action, duration = 5000, onClose, className = "", style, ...props }, ref) => {
    const [visible, setVisible] = useState(true);
    const { bg, border, icon } = variantStyles[variant];

    useEffect(() => {
      if (duration > 0) {
        const timer = setTimeout(() => {
          setVisible(false);
          setTimeout(() => onClose?.(), 240);
        }, duration);
        return () => clearTimeout(timer);
      }
    }, [duration, onClose]);

    if (!visible) return null;

    const combinedStyle: CSSProperties = {
      ...baseStyles,
      backgroundColor: bg,
      borderLeftColor: border,
      ...style,
    };

    return (
      <div
        ref={ref}
        role="alert"
        aria-live="polite"
        className={className}
        style={combinedStyle}
        {...props}
      >
        <style dangerouslySetInnerHTML={{ __html: keyframes }} />
        <span
          style={{
            fontSize: "1.25rem",
            lineHeight: 1,
            flexShrink: 0,
          }}
          aria-hidden="true"
        >
          {icon}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h4 style={{ fontFamily: "var(--font-sans)", fontSize: "0.875rem", fontWeight: "600", color: "var(--color-ink)", margin: 0, marginBottom: "var(--space-1)" }}>
            {title}
          </h4>
          {description && (
            <p style={{ fontFamily: "var(--font-sans)", fontSize: "0.8125rem", color: "var(--color-ink-soft)", margin: 0, lineHeight: 1.6 }}>
              {description}
            </p>
          )}
        </div>
        {action && (
          <div style={{ flexShrink: 0, marginLeft: "var(--space-2)" }}>
            {action}
          </div>
        )}
        <button
          type="button"
          onClick={() => { setVisible(false); setTimeout(() => onClose?.(), 240); }}
          style={closeButtonStyles}
          aria-label="Dismiss"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    );
  }
);

Toast.displayName = "Toast";

export default Toast;