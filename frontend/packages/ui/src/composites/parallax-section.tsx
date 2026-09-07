import { useEffect, useRef, type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type ParallaxSectionProps = {
  children: ReactNode;
  speed?: number;
  className?: string;
  as?: 'section' | 'div';
};

export function ParallaxSection({
  children,
  speed = 0.5,
  className,
  as = 'section',
}: ParallaxSectionProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const handleScroll = () => {
      const rect = element.getBoundingClientRect();
      const scrollPercent = (window.innerHeight - rect.top) / (window.innerHeight + rect.height);
      const clampedPercent = Math.max(0, Math.min(1, scrollPercent));
      const offset = (clampedPercent - 0.5) * speed * 100;
      element.style.transform = `translateY(${offset}px)`;
    };

    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(handleScroll);
    };

    handleScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(raf);
    };
  }, [speed]);

  const Component = as as 'div';
  return (
    <Component ref={ref} className={cn('will-change-transform', className)}>
      {children}
    </Component>
  );
}
