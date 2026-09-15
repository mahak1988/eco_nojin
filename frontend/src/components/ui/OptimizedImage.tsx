import { useState } from 'react';
import type { ImgHTMLAttributes } from 'react';

interface OptimizedImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'src' | 'srcSet'> {
  /** Image source path (relative to public folder or imported asset) */
  src: string;
  /** Alternative text for accessibility */
  alt: string;
  /** Width of the image */
  width?: number;
  /** Height of the image */
  height?: number;
  /** Sizes attribute for responsive images */
  sizes?: string;
  /** Priority loading (for above-the-fold images) */
  priority?: boolean;
  /** Loading strategy */
  loading?: 'lazy' | 'eager';
  /** CSS class name */
  className?: string;
  /** Placeholder blur data URL */
  placeholder?: string;
}

/**
 * Optimized Image component with responsive WebP/AVIF support.
 * Uses <picture> element for format negotiation and proper lazy loading.
 */
export function OptimizedImage({
  src,
  alt,
  width,
  height,
  sizes = '100vw',
  priority = false,
  loading = 'lazy',
  className = '',
  placeholder,
  ...props
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(src);

  // Generate WebP and AVIF variants
  const getWebPSrc = (src: string) => src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
  const getAVIFSrc = (src: string) => src.replace(/\.(jpg|jpeg|png)$/i, '.avif');

  const webpSrc = getWebPSrc(src);
  const avifSrc = getAVIFSrc(src);

  // If it's already a modern format, don't try to convert
  const isModernFormat = /\.(webp|avif)$/i.test(src);

  const handleLoad = () => setIsLoaded(true);
  const handleError = () => {
    // Fallback to original format on error
    if (currentSrc !== src) {
      setCurrentSrc(src);
    }
  };

  // For priority images, use eager loading
  const effectiveLoading = priority ? 'eager' : loading;

  return (
    <picture className={`relative inline-block ${className}`}>
      {/* AVIF - best compression */}
      {!isModernFormat && (
        <source
          type="image/avif"
          srcSet={avifSrc}
          sizes={sizes}
          onError={() => {}}
        />
      )}
      {/* WebP - good compression, wide support */}
      {!isModernFormat && (
        <source
          type="image/webp"
          srcSet={webpSrc}
          sizes={sizes}
          onError={() => {}}
        />
      )}
      {/* Fallback - original format */}
      <img
        src={currentSrc}
        alt={alt}
        width={width}
        height={height}
        sizes={sizes}
        loading={effectiveLoading}
        decoding={priority ? 'sync' : 'async'}
        fetchPriority={priority ? 'high' : 'auto'}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        } ${className}`}
        onLoad={handleLoad}
        onError={handleError}
        {...props}
      />
      {/* Placeholder blur effect */}
      {placeholder && !isLoaded && (
        <div
          className="absolute inset-0 bg-cover bg-center opacity-60 transition-opacity duration-500"
          style={{
            backgroundImage: `url(${placeholder})`,
            filter: 'blur(20px)',
            transform: 'scale(1.1)',
          }}
          aria-hidden="true"
        />
      )}
    </picture>
  );
}

/**
 * Generates a tiny blurred placeholder (Base64 data URL).
 * Use for LQIP (Low Quality Image Placeholders).
 */
export function generatePlaceholder(width = 20, height = 20, color = '#1a4a3a'): string {
  const svg = `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${color}"/>
    </svg>
  `;
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

/**
 * Hero image variant - optimized for above-the-fold content
 */
export function HeroImage({
  src,
  alt,
  className = '',
  ...props
}: Omit<OptimizedImageProps, 'priority' | 'loading'>) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      priority={true}
      loading="eager"
      sizes="(max-width: 768px) 100vw, 50vw"
      className={className}
      {...props}
    />
  );
}