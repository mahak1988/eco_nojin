import { useState, useRef } from 'react';
import { cn } from '../../lib/utils';

/** Card with spotlight follow effect on hover. */
export default function SpotlightCard({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [spotlight, setSpotlight] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setSpotlight({ x, y, opacity: 1 });
  };

  return (
    <div
      ref={ref}
      className={cn('spotlight-card rounded-3xl glass p-6 transition-all duration-300', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setSpotlight({ x: 50, y: 50, opacity: 0 })}
    >
      <div
        className="pointer-events-none absolute rounded-inherit opacity-0 transition-opacity duration-300"
        style={{
          left: `${spotlight.x}%`,
          top: `${spotlight.y}%`,
          width: '300px',
          height: '300px',
          transform: 'translate(-50%, -50%)',
          background: 'radial-gradient(circle, rgba(47,179,107,0.12) 0%, transparent 60%)',
          opacity: spotlight.opacity,
          pointerEvents: 'none',
        }}
        aria-hidden
      />
      {children}
    </div>
  );
}
