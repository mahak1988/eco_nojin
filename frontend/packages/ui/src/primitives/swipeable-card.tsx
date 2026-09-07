import { type ReactNode, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Archive, Trash2 } from '../primitives/icon';

export type SwipeableCardProps = {
  children: ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: ReactNode;
  rightAction?: ReactNode;
  leftActionLabel?: string;
  rightActionLabel?: string;
  disabled?: boolean;
  className?: string;
  threshold?: number;
};

export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction,
  rightAction,
  leftActionLabel = 'Archive',
  rightActionLabel = 'Delete',
  disabled = false,
  className,
  threshold = 50,
}: SwipeableCardProps) {
  const [translateX, setTranslateX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);
  const currentX = useRef(0);
  const pointerIdRef = useRef<number | null>(null);

  const handlePointerDown = (e: React.PointerEvent) => {
    if (disabled) return;
    setIsDragging(true);
    startX.current = e.clientX;
    currentX.current = e.clientX;
    pointerIdRef.current = e.pointerId;
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging || disabled) return;
    currentX.current = e.clientX;
    const delta = currentX.current - startX.current;
    setTranslateX(delta);
  };

  const handlePointerUp = () => {
    if (!isDragging || disabled) return;
    setIsDragging(false);
    const delta = translateX;

    if (delta > threshold && onSwipeRight) {
      onSwipeRight();
    } else if (delta < -threshold && onSwipeLeft) {
      onSwipeLeft();
    }

    setTranslateX(0);
    if (pointerIdRef.current !== null) {
      try {
        (document.activeElement as HTMLElement)?.releasePointerCapture?.(pointerIdRef.current);
      } catch {
        // ignore release errors
      }
      pointerIdRef.current = null;
    }
  };

  const defaultLeftAction = leftAction ?? (
    <div className="flex items-center justify-center gap-1 rounded-xl bg-sky-50 px-4 text-sky-700">
      <Archive size={18} />
      <span className="text-xs font-medium">{leftActionLabel}</span>
    </div>
  );

  const defaultRightAction = rightAction ?? (
    <div className="flex items-center justify-center gap-1 rounded-xl bg-danger/10 px-4 text-danger">
      <Trash2 size={18} />
      <span className="text-xs font-medium">{rightActionLabel}</span>
    </div>
  );

  return (
    <div className={cn('relative overflow-hidden rounded-xl', className)}>
      <div className="absolute inset-y-0 start-0 flex items-center">
        {defaultLeftAction}
      </div>
      <div className="absolute inset-y-0 end-0 flex items-center">
        {defaultRightAction}
      </div>

      <div
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={() => { setIsDragging(false); setTranslateX(0); pointerIdRef.current = null; }}
        className={cn(
          'relative bg-surface-raised transition-transform duration-200 ease-out-soft',
          isDragging && 'transition-none',
        )}
        style={{ transform: `translateX(${translateX}px)` }}
      >
        {children}
      </div>
    </div>
  );
}
