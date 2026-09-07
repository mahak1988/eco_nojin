import { useEffect, useRef, useState, type ReactNode } from 'react';
import { cn } from '@eco/utils';

export interface RevealProps {
  children: ReactNode;
  className?: string;
  /** Transition delay in ms (stagger helper). */
  delay?: number;
  /** Only animate once when scrolled into view (default true). */
  once?: boolean;
}

/**
 * Scroll-reveal wrapper. Fades/slides children in when they enter the
 * viewport. Respects `prefers-reduced-motion` (renders visible immediately).
 */
export function Reveal({ children, className, delay = 0, once = true }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setInView(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setInView(true);
            if (once) io.disconnect();
          } else if (!once) {
            setInView(false);
          }
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -48px 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [once]);

  return (
    <div
      ref={ref}
      className={cn('reveal', inView && 'in', className)}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
