"use client";

import React, { type HTMLAttributes, forwardRef, type CSSProperties } from "react";

export type SkeletonVariant = "text" | "card" | "stat" | "table-row" | "circular" | "rectangular";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  lines?: number;
}

const variantStyles: Record<SkeletonVariant, CSSProperties> = {
  text: {
    height: "1rem",
    borderRadius: "var(--radius-2)",
  },
  card: {
    borderRadius: "var(--radius-16)",
    background: "var(--color-surface)",
    border: "1px solid var(--color-line)",
    padding: "var(--space-6)",
  },
  stat: {
    borderRadius: "var(--radius-12)",
    background: "var(--color-surface)",
    border: "1px solid var(--color-line)",
    padding: "var(--space-4)",
    minWidth: "160px",
  },
  "table-row": {
    display: "grid",
    gap: "var(--space-4)",
    padding: "var(--space-3) var(--space-4)",
    borderBottom: "1px solid var(--color-line)",
  },
  circular: {
    borderRadius: "50%",
  },
  rectangular: {
    borderRadius: "var(--radius-8)",
  },
};

const baseStyles: CSSProperties = {
  background: "linear-gradient(90deg, var(--color-surface-2) 25%, var(--color-line) 50%, var(--color-surface-2) 75%)",
  backgroundSize: "200% 100%",
  animation: "shimmer 1.5s ease-in-out infinite",
};

const keyframes = `
  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
`;

const lineStyles = (lineIndex: number, totalLines: number): CSSProperties => ({
  width: lineIndex === totalLines - 1 ? "70%" : "100%",
  marginBottom: lineIndex === totalLines - 1 ? "0" : "var(--space-2)",
});

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = "text", width, height, lines = 1, className = "", style, ...props }, ref) => {
    const combinedStyle: CSSProperties = {
      ...baseStyles,
      ...variantStyles[variant],
      ...(width ? { width: typeof width === "number" ? `${width}px` : width } : {}),
      ...(height ? { height: typeof height === "number" ? `${height}px` : height } : {}),
      ...style,
    };

    if (variant === "text" && lines > 1) {
      return (
        <div
          ref={ref}
          className={className}
          style={{
            ...style,
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
          {...props}
        >
          <style dangerouslySetInnerHTML={{ __html: keyframes }} />
          {Array.from({ length: lines }).map((_, i) => (
            <div
              key={i}
              style={{
                ...baseStyles,
                ...variantStyles.text,
                ...lineStyles(i, lines),
              }}
            />
          ))}
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={className}
        style={combinedStyle}
        {...props}
      >
        <style dangerouslySetInnerHTML={{ __html: keyframes }} />
      </div>
    );
  }
);

Skeleton.displayName = "Skeleton";

export default Skeleton;