/** Animated counter hook — counts up from 0 to target value. */

import { useEffect, useState } from 'react';

interface AnimatedCounterProps {
  target: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
}

export function useAnimatedCounter(target: number, duration = 1000) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (target === 0) {
      setCurrent(0);
      return;
    }

    const startTime = Date.now();
    const startValue = 0;

    const animate = () => {
      const now = Date.now();
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easeOut = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(startValue + (target - startValue) * easeOut);

      setCurrent(value);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [target, duration]);

  return current;
}

export function AnimatedCounter({ target, duration = 1000, suffix = '', prefix = '' }: AnimatedCounterProps) {
  const current = useAnimatedCounter(target, duration);

  return (
    <span dir="ltr">
      {prefix}
      {current.toLocaleString('en-US')}
      {suffix}
    </span>
  );
}
