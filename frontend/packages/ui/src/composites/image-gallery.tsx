import { cn } from '@eco/utils'
import { useState } from 'react'
import { ChevronLeft, ChevronRight, X } from '../primitives/icon'

export type ImageGalleryProps = {
  images: { src: string; alt?: string }[]
  className?: string
}

export function ImageGallery({ images, className }: ImageGalleryProps) {
  const [index, setIndex] = useState(0)
  const [lightbox, setLightbox] = useState(false)

  if (!images || images.length === 0) return null

  const safeIndex = Math.min(index, images.length - 1)
  const prev = () => setIndex((i) => (i === 0 ? images.length - 1 : i - 1))
  const next = () => setIndex((i) => (i === images.length - 1 ? 0 : i + 1))

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div className="relative overflow-hidden rounded-lg bg-surface-muted">
        <button
          type="button"
          onClick={() => setLightbox(true)}
          className="w-full"
          aria-label="باز کردن تصویر"
        >
          <img
            src={images[safeIndex]?.src}
            alt={images[safeIndex]?.alt ?? ''}
            className="h-64 w-full object-cover"
          />
        </button>
        {images.length > 1 && (
          <>
            <button
              type="button"
              onClick={prev}
              className="absolute inset-y-0 start-2 m-auto h-8 w-8 rounded-full bg-white/80 p-1"
              aria-label="قبلی"
            >
              <ChevronRight size={16} />
            </button>
            <button
              type="button"
              onClick={next}
              className="absolute inset-y-0 end-2 m-auto h-8 w-8 rounded-full bg-white/80 p-1"
              aria-label="بعدی"
            >
              <ChevronLeft size={16} />
            </button>
          </>
        )}
      </div>
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto">
          {images.map((img, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setIndex(i)}
              className={cn(
                'h-16 w-20 shrink-0 rounded-md border-2 bg-surface-muted object-cover',
                i === index ? 'border-brand-600' : 'border-transparent',
              )}
            >
              <img
                src={img.src}
                alt={img.alt ?? ''}
                className="h-full w-full rounded-md object-cover"
              />
            </button>
          ))}
        </div>
      )}
      {lightbox && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/80 p-4">
          <button
            type="button"
            onClick={() => setLightbox(false)}
            className="absolute top-4 end-4 text-white"
            aria-label="بستن"
          >
            <X size={24} />
          </button>
          <img
            src={images[safeIndex]?.src ?? ''}
            alt={images[safeIndex]?.alt ?? ''}
            className="max-h-[85vh] max-w-[85vw] rounded-lg object-contain"
          />
        </div>
      )}
    </div>
  )
}
