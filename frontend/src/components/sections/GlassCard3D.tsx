import { useState } from 'react';
import { cn } from '../../lib/utils';

/** 3D glass card with hover elevation. */
export default function GlassCard3D({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const [style, setStyle] = useState<React.CSSProperties>({});

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -3;
    const rotateY = ((x - centerX) / centerX) * 3;
    setStyle({
      transform: `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`,
      boxShadow: `0 20px 40px -10px rgba(0,0,0,0.4), 0 0 0 1px rgba(126,226,168,0.1), inset 0 1px 0 rgba(255,255,255,0.06)`,
    });
  };

  const handleMouseLeave = () => {
    setStyle({
      transform: 'perspective(800px) rotateX(0) rotateY(0) translateZ(0)',
      boxShadow: `0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)`,
    });
  };

  return (
    <div
      className={cn('card-3d rounded-3xl glass p-6', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style}
    >
      {children}
    </div>
  );
}
