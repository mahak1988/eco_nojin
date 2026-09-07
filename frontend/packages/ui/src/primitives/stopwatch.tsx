import { type ReactNode } from 'react';
import { cn } from '@eco/utils';
import { Button } from '../primitives';
import { useStopwatch } from '../hooks/useStopwatch';
import { AnimatedCounter } from '../composites/animated-counter';

export type StopwatchProps = {
  className?: string;
  onLap?: (laps: { id: number; time: number; lapTime: number }[]) => void;
};

export function Stopwatch({ className, onLap }: StopwatchProps) {
  const { isRunning, time, start, stop, reset, lap, laps } = useStopwatch();

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const centiseconds = Math.floor((ms % 1000) / 10);
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}:${String(centiseconds).padStart(2, '0')}`;
  };

  const handleLap = () => {
    lap();
    onLap?.(laps);
  };

  return (
    <div className={cn('flex flex-col items-center gap-6', className)}>
      <div className="text-5xl font-mono font-bold text-ink tabular-nums">
        <AnimatedCounter from={0} to={time} duration={0} formatter={formatTime} />
      </div>

      <div className="flex items-center gap-3">
        {!isRunning ? (
          <Button variant="primary" onClick={start}>شروع</Button>
        ) : (
          <Button variant="secondary" onClick={stop}>توقف</Button>
        )}
        <Button variant="ghost" onClick={reset} disabled={time === 0}>بازنشانی</Button>
        {isRunning && <Button variant="ghost" onClick={handleLap}>دور</Button>}
      </div>

      {laps.length > 0 && (
        <div className="mt-4 max-h-48 w-full overflow-auto rounded-lg border border-ink/10 bg-surface-raised">
          <div className="grid grid-cols-3 gap-2 border-b border-ink/5 px-4 py-2 text-xs font-medium text-ink-muted">
            <span>دور</span>
            <span className="text-center">زمان دور</span>
            <span className="text-center">زمان کل</span>
          </div>
          {laps.map((lapItem, index) => (
            <div
              key={lapItem.id}
              className={cn(
                'grid grid-cols-3 gap-2 px-4 py-2 text-sm',
                index % 2 === 0 && 'bg-surface-muted/50',
              )}
            >
              <span className="text-ink-muted">#{index + 1}</span>
              <span className="text-center font-mono">{formatTime(lapItem.lapTime)}</span>
              <span className="text-center font-mono">{formatTime(lapItem.time)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
