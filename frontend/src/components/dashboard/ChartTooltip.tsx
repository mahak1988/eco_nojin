/** Custom tooltip for charts — glass style with smooth animation. */

import { useRef } from 'react';

interface ChartTooltipProps {
  x: number;
  y: number;
  visible: boolean;
  children: React.ReactNode;
}

export default function ChartTooltip({ x, y, visible, children }: ChartTooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);

  if (!visible) return null;

  return (
    <div
      ref={tooltipRef}
      className="glass-advanced fixed z-50 min-w-48 rounded-xl px-4 py-3 shadow-2xl"
      style={{
        left: `${x + 12}px`,
        top: `${y - 12}px`,
        pointerEvents: 'none',
      }}
    >
      {children}
    </div>
  );
}

interface TooltipContentProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
}

export function TooltipContent({ title, value, unit, subtitle }: TooltipContentProps) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs font-extrabold text-[var(--color-night-100)]">{title}</p>
      <p className="text-lg font-extrabold text-gradient-leaf" dir="ltr">
        {value}
        {unit && <span className="text-xs text-[var(--color-night-200)]"> {unit}</span>}
      </p>
      {subtitle && <p className="text-[10px] text-[var(--color-night-200)]">{subtitle}</p>}
    </div>
  );
}
