import { useState } from 'react';
import { cn } from '../../lib/utils';

/** Interactive card with 3D tilt following mouse. */
export default function TiltCard3D({
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
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rx = ((y - cy) / cy) * -8;
    const ry = ((x - cx) / cx) * 8;
    setStyle({
      transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) scale3d(1.02,1.02,1.02)`,
      boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
    });
  };

  const handleMouseLeave = () => {
    setStyle({
      transform: 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1,1,1)',
      boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
    });
  };

  return (
    <div
      className={cn('rounded-3xl glass p-6 transition-all duration-200', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style}
    >
      {children}
    </div>
  );
}
