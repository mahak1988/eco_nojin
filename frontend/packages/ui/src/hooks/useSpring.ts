import { useEffect, useRef } from 'react';

export type SpringConfig = {
  tension?: number;
  friction?: number;
  mass?: number;
  velocity?: number;
};

const DEFAULT_CONFIG: Required<SpringConfig> = {
  tension: 170,
  friction: 26,
  mass: 1,
  velocity: 0,
};

export function useSpring(
  target: number,
  config: SpringConfig = {},
  deps: unknown[] = [],
) {
  const merged = { ...DEFAULT_CONFIG, ...config };
  const current = useRef(target);
  const velocity = useRef(merged.velocity);
  const raf = useRef<number>(0);

  useEffect(() => {
    const start = current.current;
    const startTime = performance.now();
    const duration = 1000;

    const step = () => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      current.current = start + (target - start) * eased;
      if (progress < 1) {
        raf.current = requestAnimationFrame(step);
      }
    };

    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [target, ...deps]);

  return current.current;
}
