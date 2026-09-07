import { type ReactNode, useRef } from 'react';
import { cn } from '@eco/utils';

export type ThreeDIllustrationProps = {
  children: ReactNode;
  className?: string;
  rotateX?: number;
  rotateY?: number;
  rotateZ?: number;
  scale?: number;
  perspective?: number;
  interactive?: boolean;
};

export function ThreeDIllustration({
  children,
  className,
  rotateX = 0,
  rotateY = 0,
  rotateZ = 0,
  scale = 1,
  perspective = 1000,
  interactive = false,
}: ThreeDIllustrationProps) {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!interactive || !ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateY = ((x - centerX) / centerX) * 20;
    const rotateX = -((y - centerY) / centerY) * 20;

    ref.current.style.transform = `perspective(${perspective}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`;
  };

  const handleMouseLeave = () => {
    if (!ref.current) return;
    ref.current.style.transform = `perspective(${perspective}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) rotateZ(${rotateZ}deg) scale(${scale})`;
  };

  return (
    <div
      ref={ref}
      className={cn('transform-gpu transition-transform duration-300 ease-out-soft', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: `perspective(${perspective}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) rotateZ(${rotateZ}deg) scale(${scale})`,
      }}
    >
      {children}
    </div>
  );
}
