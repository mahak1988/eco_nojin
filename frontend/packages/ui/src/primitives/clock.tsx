import { useEffect, useState } from 'react';
import { cn } from '@eco/utils';

export type ClockProps = {
  className?: string;
  showSeconds?: boolean;
  hour12?: boolean;
  timeZone?: string;
};

export function Clock({ className, showSeconds = true, hour12 = false, timeZone }: ClockProps) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const formatTime = (date: Date) => {
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();
    const ampm = hour12 ? (hours >= 12 ? 'PM' : 'AM') : undefined;
    if (hour12 && hours >= 12) hours -= 12;
    if (hour12 && hours === 0) hours = 12;

    const pad = (n: number) => String(n).padStart(2, '0');
    const timeStr = `${pad(hours)}:${pad(minutes)}${showSeconds ? `:${pad(seconds)}` : ''}`;
    return ampm ? `${timeStr} ${ampm}` : timeStr;
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fa-IR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone,
    });
  };

  return (
    <div className={cn('flex flex-col items-center gap-1', className)}>
      <div className="text-3xl font-bold font-mono tabular-nums text-ink">{formatTime(time)}</div>
      <div className="text-xs text-ink-muted">{formatDate(time)}</div>
    </div>
  );
}
