import { useCallback, useEffect, useRef, useState } from 'react';

export type StopwatchLap = {
  id: number;
  time: number;
  lapTime: number;
};

export type UseStopwatchResult = {
  isRunning: boolean;
  time: number;
  start: () => void;
  stop: () => void;
  reset: () => void;
  lap: () => void;
  laps: StopwatchLap[];
};

export function useStopwatch(): UseStopwatchResult {
  const [isRunning, setIsRunning] = useState(false);
  const [time, setTime] = useState(0);
  const [laps, setLaps] = useState<StopwatchLap[]>([]);
  const startTimeRef = useRef(0);
  const elapsedRef = useRef(0);
  const rafRef = useRef<number>(0);
  const lapIdRef = useRef(0);

  const update = useCallback(() => {
    const now = performance.now();
    setTime(elapsedRef.current + (now - startTimeRef.current));
    rafRef.current = requestAnimationFrame(update);
  }, []);

  const start = useCallback(() => {
    if (isRunning) return;
    startTimeRef.current = performance.now();
    rafRef.current = requestAnimationFrame(update);
    setIsRunning(true);
  }, [isRunning, update]);

  const stop = useCallback(() => {
    if (!isRunning) return;
    cancelAnimationFrame(rafRef.current);
    elapsedRef.current += performance.now() - startTimeRef.current;
    setIsRunning(false);
  }, [isRunning]);

  const reset = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    setIsRunning(false);
    setTime(0);
    setLaps([]);
    elapsedRef.current = 0;
    lapIdRef.current = 0;
  }, []);

  const lap = useCallback(() => {
    if (!isRunning) return;
    const current = time;
    const previousLap = laps.length > 0 ? laps[laps.length - 1]?.time ?? 0 : 0;
    setLaps((prev) => [...prev, { id: lapIdRef.current++, time: current, lapTime: current - previousLap }]);
  }, [isRunning, time, laps]);

  useEffect(() => {
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  return { isRunning, time, start, stop, reset, lap, laps };
}
