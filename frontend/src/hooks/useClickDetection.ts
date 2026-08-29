import { useRef, useCallback } from 'react';

/**
 * Scientific click-vs-drag detection
 * Uses timing + distance thresholds to distinguish clicks from drags
 * 
 * Algorithm:
 *   CLICK if: (duration < 200ms) AND (distance < 5px)
 *   DRAG otherwise
 */
export function useClickDetection(
  onClick: (event: any) => void,
  options: { maxDuration?: number; maxDistance?: number } = {}
) {
  const { maxDuration = 200, maxDistance = 5 } = options;
  const downTime = useRef<number>(0);
  const downPos = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const isDragging = useRef(false);

  const onPointerDown = useCallback((e: any) => {
    downTime.current = Date.now();
    downPos.current = { x: e.clientX ?? e.pointer?.x ?? 0, y: e.clientY ?? e.pointer?.y ?? 0 };
    isDragging.current = false;
  }, []);

  const onPointerMove = useCallback((e: any) => {
    if (downTime.current === 0) return;
    const x = e.clientX ?? e.pointer?.x ?? 0;
    const y = e.clientY ?? e.pointer?.y ?? 0;
    const dx = x - downPos.current.x;
    const dy = y - downPos.current.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxDistance) {
      isDragging.current = true;
    }
  }, [maxDistance]);

  const onPointerUp = useCallback((e: any) => {
    if (downTime.current === 0) return;
    const duration = Date.now() - downTime.current;
    const x = e.clientX ?? e.pointer?.x ?? 0;
    const y = e.clientY ?? e.pointer?.y ?? 0;
    const dx = x - downPos.current.x;
    const dy = y - downPos.current.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (duration < maxDuration && distance < maxDistance && !isDragging.current) {
      // This is a genuine CLICK
      onClick(e);
    }
    // Reset
    downTime.current = 0;
    isDragging.current = false;
  }, [onClick, maxDuration, maxDistance]);

  return { onPointerDown, onPointerMove, onPointerUp };
}

/**
 * Hook to detect long press (for context menus)
 */
export function useLongPress(
  onLongPress: (event: any) => void,
  duration: number = 500
) {
  const timerRef = useRef<number | null>(null);

  const onPointerDown = useCallback((e: any) => {
    timerRef.current = window.setTimeout(() => {
      onLongPress(e);
    }, duration);
  }, [onLongPress, duration]);

  const onPointerUp = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  return { onPointerDown, onPointerUp };
}
