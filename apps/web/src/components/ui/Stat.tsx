"use client";

import React, { type ReactNode, forwardRef, type HTMLAttributes, type CSSProperties } from "react";

export interface ProvenanceStampProps {
  source?: string;
  verified?: boolean;
  timestamp?: string;
  method?: string;
}

export interface StatProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  provenance?: ProvenanceStampProps;
  size?: "sm" | "md" | "lg";
}

const sizeStyles: Record<"sm" | "md" | "lg", CSSProperties> = {
  sm: { fontSize: "1.5rem", gap: "var(--space-1)" },
  md: { fontSize: "2.5rem", gap: "var(--space-2)" },
  lg: { fontSize: "3.5rem", gap: "var(--space-3)" },
};

const baseStyles: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  fontFamily: "var(--font-mono)",
  fontVariantNumeric: "tabular-nums",
  direction: "ltr",
  unicodeBidi: "isolate",
  color: "var(--color-ink)",
};

const labelStyles: CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "0.875rem",
  fontWeight: 500,
  color: "var(--color-ink-soft)",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
};

const trendStyles: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "var(--space-1)",
  fontFamily: "var(--font-sans)",
  fontSize: "0.8125rem",
  fontWeight: 600,
};

const provenanceStyles: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "var(--space-2)",
  marginTop: "var(--space-3)",
  paddingTop: "var(--space-3)",
  borderTop: "1px solid var(--color-line)",
  fontFamily: "var(--font-sans)",
  fontSize: "0.6875rem",
  color: "var(--color-ink-faint)",
};

export const Stat = forwardRef<HTMLDivElement, StatProps>(
  (
    {
      label,
      value,
      unit,
      trend,
      trendValue,
      provenance,
      size = "md",
      className = "",
      style,
      children,
      ...props
    },
    ref
  ) => {
    const combinedStyle: CSSProperties = {
      ...baseStyles,
      ...sizeStyles[size],
      ...style,
    };

    const trendColor = trend === "up" ? "var(--color-forest)" : trend === "down" ? "var(--color-copper)" : "var(--color-ink-soft)";

    return (
      <div
        ref={ref}
        className={className}
        style={combinedStyle}
        {...props}
      >
        <span style={labelStyles}>{label}</span>
        <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-1)" }}>
          <span>{value}</span>
          {unit && <span style={{ fontSize: "0.75em", color: "var(--color-ink-soft)" }}>{unit}</span>}
        </div>
        {(trend || trendValue) && (
          <div style={{ ...trendStyles, color: trendColor }}>
            {trend === "up" && <span aria-hidden="true">▲</span>}
            {trend === "down" && <span aria-hidden="true">▼</span>}
            {trend === "neutral" && <span aria-hidden="true">—</span>}
            {trendValue && <span>{trendValue}</span>}
          </div>
        )}
        {provenance && (
          <div style={provenanceStyles}>
            <span aria-hidden="true">🔬</span>
            <span>{provenance.source || "Unknown source"}</span>
            {provenance.verified && <span aria-label="Verified">✓</span>}
            {provenance.method && <span>· {provenance.method}</span>}
            {provenance.timestamp && <span>· {new Date(provenance.timestamp).toLocaleDateString()}</span>}
          </div>
        )}
        {children}
      </div>
    );
  }
);

Stat.displayName = "Stat";

export default Stat;