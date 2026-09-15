import { useRef, useState, useEffect } from 'react';
import { cn } from '../../lib/utils';

/** Section with parallax scroll effect. */
export default function ParallaxSection({
  children,
  className,
  offset = 0.3,
}: {
  children: React.ReactNode;
  className?: string;
  offset?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [offsetY, setOffsetY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      if (ref.current) {
        const rect = ref.current.getBoundingClientRect();
        setOffsetY(rect.top * offset);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [offset]);

  return (
    <div ref={ref} className={cn('transition-transform duration-100 ease-out', className)} style={{ transform: `translateY(${offsetY}px)` }}>
      {children}
    </div>
  );
}
