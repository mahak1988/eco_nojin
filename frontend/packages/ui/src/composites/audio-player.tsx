import { cn } from '@eco/utils'
import { useRef, useState } from 'react'
import { Button } from '../primitives'
import { Pause, Play, SkipBack, SkipForward } from '../primitives/icon'

export type AudioTrack = {
  title: string
  artist?: string
  src: string
}

export type AudioPlayerProps = {
  tracks: AudioTrack[]
  className?: string
}

export function AudioPlayer({ tracks, className }: AudioPlayerProps) {
  const [current, setCurrent] = useState(0)
  const [playing, setPlaying] = useState(false)
  const ref = useRef<HTMLAudioElement>(null)

  const toggle = () => {
    if (ref.current?.paused) {
      ref.current.play()
      setPlaying(true)
    } else {
      ref.current?.pause()
      setPlaying(false)
    }
  }

  const prev = () => setCurrent((c) => (c === 0 ? tracks.length - 1 : c - 1))
  const next = () => setCurrent((c) => (c === tracks.length - 1 ? 0 : c + 1))

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border border-ink/10 bg-surface-raised p-3',
        className,
      )}
    >
      <audio ref={ref} src={tracks[current]?.src} onEnded={next} />
      <Button variant="ghost" size="sm" onClick={prev}>
        <SkipBack size={16} />
      </Button>
      <Button variant="primary" size="sm" onClick={toggle}>
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </Button>
      <Button variant="ghost" size="sm" onClick={next}>
        <SkipForward size={16} />
      </Button>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-ink">{tracks[current]?.title}</p>
        {tracks[current]?.artist && (
          <p className="truncate text-xs text-ink-muted">{tracks[current].artist}</p>
        )}
      </div>
    </div>
  )
}
