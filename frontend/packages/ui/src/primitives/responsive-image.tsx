import { type ImgHTMLAttributes } from 'react';
import { cn } from '@eco/utils';

export type ResponsiveImageProps = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src'> & {
  src: string;
  srcSet?: string;
  sizes?: string;
  alt: string;
  fallbackSrc?: string;
  className?: string;
};

export function ResponsiveImage({
  src,
  srcSet,
  sizes,
  alt,
  fallbackSrc,
  className,
  ...rest
}: ResponsiveImageProps) {
  return (
    <img
      src={src}
      srcSet={srcSet}
      sizes={sizes}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={(e) => {
        if (fallbackSrc) {
          (e.target as HTMLImageElement).src = fallbackSrc;
        }
      }}
      className={cn('h-full w-full object-cover', className)}
      {...rest}
    />
  );
}
