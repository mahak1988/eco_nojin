import { cn } from '@eco/utils'
import { type ImgHTMLAttributes, useEffect, useId, useRef, useState } from 'react'
import { Skeleton } from '../primitives/skeleton'

export type LazyImageProps = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src'> & {
  src: string
  alt: string
  width?: number
  height?: number
  placeholder?: 'shimmer' | 'blur' | 'none'
  blurDataURL?: string
  onError?: () => void
}

export function LazyImage({
  src,
  alt,
  width,
  height,
  placeholder = 'shimmer',
  blurDataURL,
  onError,
  className,
  ...rest
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const generatedId = useId()
  const imgId = `lazy-img-${generatedId}`

  useEffect(() => {
    const element = containerRef.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      { rootMargin: '100px' },
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const aspectRatio = width && height ? `${width} / ${height}` : undefined

  return (
    <div
      ref={containerRef}
      className={cn('relative overflow-hidden bg-surface-muted', className)}
      style={{ aspectRatio }}
    >
      {!isLoaded && !hasError && (
        <div className="absolute inset-0" aria-hidden="true">
          {placeholder === 'shimmer' && <Skeleton className="h-full w-full" />}
          {placeholder === 'blur' && blurDataURL && (
            <img
              src={blurDataURL}
              alt=""
              className="h-full w-full object-cover blur-sm"
              aria-hidden="true"
            />
          )}
        </div>
      )}

      {isInView && !hasError && (
        <img
          ref={imgRef}
          id={imgId}
          src={src}
          alt={alt}
          width={width}
          height={height}
          loading="lazy"
          decoding="async"
          fetchPriority="low"
          onLoad={() => setIsLoaded(true)}
          onError={() => {
            setHasError(true)
            onError?.()
          }}
          className={cn(
            'h-full w-full object-cover transition-opacity duration-300',
            isLoaded ? 'opacity-100' : 'opacity-0',
          )}
          {...rest}
        />
      )}

      {hasError && (
        <div className="flex h-full w-full items-center justify-center bg-surface-muted">
          <div className="flex flex-col items-center gap-2 text-center">
            <span className="text-2xl text-ink-subtle">🖼️</span>
            <p className="text-xs text-ink-muted">Unable to load image</p>
          </div>
        </div>
      )}

      <span className="sr-only" aria-live="polite">
        {isLoaded ? 'Image loaded' : hasError ? 'Image failed to load' : 'Loading image'}
      </span>
    </div>
  )
}
