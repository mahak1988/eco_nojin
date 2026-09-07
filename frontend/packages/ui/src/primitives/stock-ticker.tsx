import { useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';

export type StockItem = {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
};

export type StockTickerProps = {
  items: StockItem[];
  className?: string;
  speed?: number;
};

export function StockTicker({ items, className, speed = 30 }: StockTickerProps) {
  const [isPaused, setIsPaused] = useState(false);
  const [duplicatedItems, setDuplicatedItems] = useState<StockItem[]>([]);
  const tickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDuplicatedItems([...items, ...items]);
  }, [items]);

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${((change / (items[0]?.price || 1)) * 100).toFixed(2)}%)`;
  };

  return (
    <div
      className={cn('relative w-full overflow-hidden rounded-lg border border-ink/10 bg-surface-raised py-2', className)}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div
        ref={tickerRef}
        className="flex whitespace-nowrap"
        style={{
          animation: `ticker ${speed}s linear infinite`,
          animationPlayState: isPaused ? 'paused' : 'running',
        }}
      >
        {duplicatedItems.map((item, index) => (
          <div
            key={index}
            className={cn(
              'mx-4 flex items-center gap-2 text-sm',
              item.change >= 0 ? 'text-success' : 'text-danger',
            )}
          >
            <span className="font-semibold text-ink">{item.symbol}</span>
            <span className="font-mono">{item.price.toLocaleString('fa-IR')}</span>
            <span className="text-xs">
              {formatChange(item.change)}
            </span>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
