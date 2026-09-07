import { useEffect, useId, useRef, useState } from 'react';
import { cn } from '@eco/utils';

export type AnimatedLogoProps = {
  variant?: 'full' | 'icon' | 'wordmark';
  animation?: 'reveal' | 'pulse' | 'none';
  size?: number;
  className?: string;
  'aria-label'?: string;
};

export function AnimatedLogo({
  variant = 'full',
  animation = 'reveal',
  size = 32,
  className,
  'aria-label': ariaLabel = 'Eco Nojin',
}: AnimatedLogoProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimated, setIsAnimated] = useState(false);
  const generatedId = useId();
  const logoRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
      if (animation === 'reveal') {
        setTimeout(() => setIsAnimated(true), 50);
      } else {
        setIsAnimated(true);
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [animation]);

  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const shouldAnimate = animation !== 'none' && !prefersReducedMotion;

  return (
    <div
      className={cn('inline-flex items-center justify-center', className)}
      style={{ width: size, height: size }}
      aria-label={ariaLabel}
      role="img"
    >
      <svg
        ref={logoRef}
        viewBox="0 0 24 24"
        className={cn(
          'h-full w-full',
          shouldAnimate && animation === 'reveal' && isVisible && 'animate-in-up',
          shouldAnimate && animation === 'pulse' && isAnimated && 'animate-pulse',
        )}
        style={{
          animationDuration: shouldAnimate && animation === 'reveal' ? '0.6s' : undefined,
          animationDelay: shouldAnimate && animation === 'reveal' ? '0.1s' : undefined,
        }}
      >
        <defs>
          <linearGradient id={`logo-gradient-${generatedId}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#16a34a" />
            <stop offset="100%" stopColor="#0ea5e9" />
          </linearGradient>
        </defs>

        {variant === 'full' && (
          <g>
            <path
              d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"
              fill={`url(#logo-gradient-${generatedId})`}
              opacity={isAnimated ? 1 : 0}
              style={{ transition: 'opacity 0.3s ease-out 0.1s' }}
            />
            <path
              d="M2 21c0-3 1.9-5.4 5.1-6C9.5 14.5 12 13 13 12"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              opacity={isAnimated ? 1 : 0}
              style={{ transition: 'opacity 0.3s ease-out 0.2s' }}
            />
            {variant === 'full' && (
              <text x="14" y="16" fontSize="6" fontWeight="bold" fill="currentColor" opacity={isAnimated ? 1 : 0} style={{ transition: 'opacity 0.3s ease-out 0.3s' }}>
                EN
              </text>
            )}
          </g>
        )}

        {variant === 'icon' && (
          <path
            d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"
            fill={`url(#logo-gradient-${generatedId})`}
            opacity={isAnimated ? 1 : 0}
            style={{ transition: 'opacity 0.3s ease-out 0.1s' }}
          />
        )}

        {variant === 'wordmark' && (
          <text x="2" y="16" fontSize="8" fontWeight="bold" fill="currentColor" opacity={isAnimated ? 1 : 0} style={{ transition: 'opacity 0.3s ease-out 0.1s' }}>
            Eco Nojin
          </text>
        )}
      </svg>
    </div>
  );
}
