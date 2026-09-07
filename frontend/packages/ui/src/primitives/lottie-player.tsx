import { useEffect, useRef, type ImgHTMLAttributes } from 'react';
import lottie, { type AnimationItem } from 'lottie-web';
import { cn } from '@eco/utils';

export type LottiePlayerProps = {
  src: string | object;
  loop?: boolean;
  autoplay?: boolean;
  speed?: number;
  className?: string;
  onComplete?: () => void;
  onReady?: (animation: AnimationItem) => void;
  width?: number | string;
  height?: number | string;
};

export function LottiePlayer({
  src,
  loop = true,
  autoplay = true,
  speed = 1,
  className,
  onComplete,
  onReady,
  width = '100%',
  height = '100%',
}: LottiePlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<AnimationItem | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const animation = lottie.loadAnimation({
      container: containerRef.current,
      renderer: 'svg',
      loop,
      autoplay,
      animationData: typeof src === 'string' ? { path: src } : src,
    });

    animation.setSpeed(speed);
    animation.addEventListener('complete', () => onComplete?.());
    if (onReady) {
      animation.addEventListener('DOMLoaded', () => onReady(animation));
    }
    animationRef.current = animation;

    return () => {
      animation.removeEventListener('complete', onComplete ?? (() => {}));
      if (onReady) {
        animation.removeEventListener('DOMLoaded', () => onReady(animation));
      }
      animation.destroy();
      animationRef.current = null;
    };
  }, [src, loop, autoplay, speed, onComplete, onReady]);

  return (
    <div
      ref={containerRef}
      className={cn('overflow-hidden', className)}
      style={{ width, height }}
      aria-label="Lottie animation"
      role="img"
    />
  );
}

export type LottieIconProps = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src' | 'width' | 'height'> & {
  src: string | object;
  size?: number;
  loop?: boolean;
  autoplay?: boolean;
};

export function LottieIcon({
  src,
  size = 24,
  loop = true,
  autoplay = true,
  className,
  ...rest
}: LottieIconProps) {
  return (
    <LottiePlayer
      src={src}
      loop={loop}
      autoplay={autoplay}
      className={cn('inline-block', className)}
      width={size}
      height={size}
      {...rest}
    />
  );
}
