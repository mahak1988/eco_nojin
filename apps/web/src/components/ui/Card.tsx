"use client";

import React, { type ReactNode, type HTMLAttributes, forwardRef, type CSSProperties } from "react";

export type CardDensity = "cozy" | "compact" | "dense";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  density?: CardDensity;
  children: ReactNode;
}

const densityStyles: Record<CardDensity, CSSProperties> = {
  cozy: {
    padding: "var(--space-6)",
    gap: "var(--space-4)",
  },
  compact: {
    padding: "var(--space-4)",
    gap: "var(--space-3)",
  },
  dense: {
    padding: "var(--space-3)",
    gap: "var(--space-2)",
  },
};

const baseStyles: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-line)",
  borderRadius: "var(--radius-16)",
  boxShadow: "var(--shadow-card)",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ density = "cozy", children, className = "", style, ...props }, ref) => {
    const combinedStyle: CSSProperties = {
      ...baseStyles,
      ...densityStyles[density],
      ...style,
    };

    return (
      <div
        ref={ref}
        className={className}
        style={combinedStyle}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export default Card;