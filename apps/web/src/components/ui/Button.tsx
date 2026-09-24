"use client";

import React, { forwardRef, type ButtonHTMLAttributes, type ReactNode, type CSSProperties } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, CSSProperties> = {
  primary: {
    backgroundColor: "var(--color-forest)",
    color: "var(--color-paper)",
    border: "1px solid var(--color-forest)",
  },
  secondary: {
    backgroundColor: "var(--color-surface)",
    color: "var(--color-ink)",
    border: "1px solid var(--color-line)",
  },
  ghost: {
    backgroundColor: "transparent",
    color: "var(--color-ink)",
    border: "1px solid transparent",
  },
  danger: {
    backgroundColor: "var(--color-copper)",
    color: "var(--color-paper)",
    border: "1px solid var(--color-copper)",
  },
};

const sizeStyles: Record<ButtonSize, CSSProperties> = {
  sm: {
    padding: "var(--space-2) var(--space-3)",
    fontSize: "0.8125rem",
    gap: "var(--space-2)",
  },
  md: {
    padding: "var(--space-3) var(--space-4)",
    fontSize: "0.875rem",
    gap: "var(--space-2)",
  },
  lg: {
    padding: "var(--space-4) var(--space-6)",
    fontSize: "1rem",
    gap: "var(--space-3)",
  },
};

const baseStyles: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily: "var(--font-sans)",
  fontWeight: 600,
  lineHeight: 1.6,
  borderRadius: "var(--radius-8)",
  transition: [
    "background-color var(--duration-120) var(--easing-ease-out-quart)",
    "border-color var(--duration-120) var(--easing-ease-out-quart)",
    "color var(--duration-120) var(--easing-ease-out-quart)",
    "opacity var(--duration-120) var(--easing-ease-out-quart)",
    "transform var(--duration-120) var(--easing-ease-out-quart)",
  ].join(", "),
  cursor: "pointer",
  textDecoration: "none",
  whiteSpace: "nowrap",
};

const spinnerStyles: CSSProperties = {
  animation: "spin 1s linear infinite",
  width: "1em",
  height: "1em",
  border: "2px solid currentColor",
  borderRightColor: "transparent",
  borderRadius: "50%",
};

const keyframes = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading = false, disabled, children, className = "", style, ...props }, ref) => {
    const isDisabled = disabled || loading;

    const combinedStyle: CSSProperties = {
      ...baseStyles,
      ...variantStyles[variant],
      ...sizeStyles[size],
      ...style,
    };

    return (
      <>
        <style dangerouslySetInnerHTML={{ __html: keyframes }} />
        <button
          ref={ref}
          type="button"
          disabled={isDisabled}
          aria-disabled={isDisabled}
          aria-busy={loading}
          className={className}
          style={combinedStyle}
          {...props}
        >
          {loading && (
            <svg
              aria-hidden="true"
              focusable="false"
              style={spinnerStyles}
              viewBox="0 0 24 24"
            >
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" />
            </svg>
          )}
          <span style={{ opacity: loading ? 0 : 1 }}>{children}</span>
        </button>
      </>
    );
  }
);

Button.displayName = "Button";

export default Button;