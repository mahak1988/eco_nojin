import { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';

/** API connection status indicator. */
export default function ConnectionStatus({ endpoint = '/api/health' }: { endpoint?: string }) {
  const [status, setStatus] = useState<'connected' | 'connecting' | 'error'>('connecting');

  useEffect(() => {
    const check = async () => {
      setStatus('connecting');
      try {
        await fetch(endpoint, { method: 'HEAD', mode: 'no-cors' });
      } catch {
        setStatus('error');
      }
    };
    check();
    const timer = setInterval(check, 30000);
    return () => clearInterval(timer);
  }, [endpoint]);

  const colors = {
    connected: 'bg-[var(--color-leaf-500)]',
    connecting: 'bg-[var(--color-sand-400)]',
    error: 'bg-red-500',
  };

  const labels = {
    connected: 'connected',
    connecting: 'connecting',
    error: 'error',
  };

  return (
    <div className="flex items-center gap-2 rounded-full glass px-3 py-1.5">
      <span className={cn('h-2 w-2 rounded-full animate-pulse-soft', colors[status])} aria-hidden />
      <span className="text-[10px] text-[var(--color-night-200)]/60 font-bold">{labels[status]}</span>
    </div>
  );
}
