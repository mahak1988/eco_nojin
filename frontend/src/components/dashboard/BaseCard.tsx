/** Base card component for dashboard widgets.
 *
 * Provides consistent glass styling, reveal animation, and layout
 * for all dashboard metric cards.
 */

import { type ReactNode } from 'react';
import Reveal from '../ui/Reveal';

export type CardVariant = 'leaf' | 'sand' | 'aqua' | 'night';

const variantCls: Record<CardVariant, string> = {
  leaf: 'bg-[var(--color-leaf-500)]/10 border-[var(--color-leaf-500)]/25',
  sand: 'bg-[var(--color-sand-500)]/10 border-[var(--color-sand-500)]/25',
  aqua: 'bg-[var(--color-aqua-500)]/10 border-[var(--color-aqua-500)]/25',
  night: 'bg-[var(--color-night-800)]/60 border-[var(--color-night-700)]/50',
};

interface BaseCardProps {
  title?: string;
  kicker?: ReactNode;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  horizontal?: boolean;
  variant?: CardVariant;
  tooltip?: string;
  onClick?: () => void;
  draggable?: boolean;
  onDragStart?: () => void;
  onDragOver?: () => void;
  onDrop?: () => void;
  onDragEnd?: () => void;
  isDragging?: boolean;
  isOver?: boolean;
}

export default function BaseCard({
  title,
  kicker,
  icon,
  children,
  className,
  horizontal,
  variant = 'night',
  tooltip,
  onClick,
  draggable,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragging,
  isOver,
}: BaseCardProps) {
  const base = variantCls[variant];
  const containerCls = horizontal
    ? `${base} glass-hover hover-lift flex flex-col gap-2 rounded-2xl p-5 sm:flex-row sm:items-center sm:justify-between`
    : `${base} glass-hover hover-lift flex flex-col gap-2 rounded-2xl p-5`;

  const dragCls = draggable
    ? 'cursor-grab active:cursor-grabbing'
    : onClick
      ? 'cursor-pointer'
      : '';

  const dragStateCls = isDragging
    ? 'scale-[0.97] opacity-60'
    : isOver
      ? 'ring-2 ring-[var(--color-leaf-500)] scale-[1.01]'
      : '';

  const cardInner = (
    <Reveal
      className={`${containerCls} ${dragCls} ${dragStateCls} ${className ?? ''}`}
      onClick={onClick}
    >
      {kicker ? (
        <span className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--color-leaf-500)] bg-[var(--color-leaf-500)] px-3 py-1 text-[11px] font-bold text-[var(--color-leaf-300)]">
          {kicker}
        </span>
      ) : null}
      {title ? (
        <h2 className="flex items-center gap-2 text-xs font-extrabold text-[var(--color-night-100)]">
          {icon}
          {title}
        </h2>
      ) : null}
      {children}
    </Reveal>
  );

  const cardWrapper = (
    <div
      draggable={draggable}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
      className="contents"
    >
      {cardInner}
    </div>
  );

  if (tooltip) {
    return (
      <div className="relative group" title={tooltip}>
        {cardWrapper}
        <div className="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
          <div className="glass-advanced rounded-xl px-4 py-3 shadow-2xl max-w-xs">
            <p className="text-xs text-[var(--color-night-200)]">{tooltip}</p>
          </div>
        </div>
      </div>
    );
  }

  return cardWrapper;
}
