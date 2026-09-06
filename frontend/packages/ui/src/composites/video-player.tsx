import { cn } from '@eco/utils'
import { useRef } from 'react'
import { Button } from '../primitives'
import { Maximize, Pause, Play, Volume2 } from '../primitives/icon'

export type VideoPlayerProps = {
  src: string
  poster?: string
  className?: string
}

export function VideoPlayer({ src, poster, className }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement>(null)
  const toggle = () => (ref.current?.paused ? ref.current.play() : ref.current?.pause())

  return (
    <div className={cn('relative overflow-hidden rounded-lg bg-black', className)}>
      <video ref={ref} src={src} poster={poster} className="h-full w-full" controls={false} />
      <div className="absolute inset-x-0 bottom-0 flex items-center gap-2 bg-gradient-to-t from-black/60 to-transparent p-3">
        <Button variant="ghost" size="sm" onClick={toggle} className="text-white">
          {ref.current?.paused ? <Play size={18} /> : <Pause size={18} />}
        </Button>
        <Button variant="ghost" size="sm" className="text-white">
          <Volume2 size={18} />
        </Button>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="sm"
          className="text-white"
          onClick={() => ref.current?.requestFullscreen?.()}
        >
          <Maximize size={18} />
        </Button>
      </div>
    </div>
  )
}
