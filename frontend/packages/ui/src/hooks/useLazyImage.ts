import { useEffect, useRef, useState } from 'react'

export type UseLazyImageOptions = {
  src: string
  rootMargin?: string
  threshold?: number
  onLoad?: () => void
  onError?: () => void
}

export type UseLazyImageResult = {
  ref: React.Ref<HTMLDivElement>
  isInView: boolean
  isLoaded: boolean
  hasError: boolean
  imageSrc: string | undefined
}

export function useLazyImage({
  src,
  rootMargin = '100px',
  threshold = 0.01,
  onLoad,
  onError,
}: UseLazyImageOptions): UseLazyImageResult {
  const [isInView, setIsInView] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = containerRef.current
    if (!element) return

    setIsLoaded(false)
    setHasError(false)

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      { rootMargin, threshold },
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [src, rootMargin, threshold])

  const handleImageLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleImageError = () => {
    setHasError(true)
    onError?.()
  }

  return {
    ref: containerRef,
    isInView,
    isLoaded,
    hasError,
    imageSrc: isInView ? src : undefined,
  }
}
