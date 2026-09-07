import { type ReactNode, useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Spinner } from '../primitives';

export type InfiniteScrollProps = {
  children: ReactNode;
  onLoadMore: () => Promise<void> | void;
  hasMore: boolean;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
  threshold?: number;
  loader?: ReactNode;
  endMessage?: ReactNode;
};

type Status = 'idle' | 'loading' | 'success' | 'error' | 'complete';

export function InfiniteScroll({
  children,
  onLoadMore,
  hasMore,
  loading = false,
  error = null,
  onRetry,
  className,
  threshold = 200,
  loader,
  endMessage,
}: InfiniteScrollProps) {
  const [status, setStatus] = useState<Status>('idle');
  const observerRef = useRef<HTMLDivElement>(null);
  const isFirstLoad = useRef(true);

  useEffect(() => {
    if (loading) {
      setStatus('loading');
      return;
    }

    if (error) {
      setStatus('error');
      return;
    }

    if (!hasMore) {
      setStatus('complete');
      return;
    }

    if (isFirstLoad.current) {
      setStatus('success');
      isFirstLoad.current = false;
    }
  }, [loading, error, hasMore]);

  useEffect(() => {
    const element = observerRef.current;
    if (!element || !hasMore || status === 'loading' || status === 'error') return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting && hasMore && !loading) {
          setStatus('loading');
          onLoadMore();
        }
      },
      { rootMargin: `${threshold}px` },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [hasMore, loading, status, onLoadMore, threshold]);

  return (
    <div className={cn('flex flex-col', className)}>
      <div className="flex flex-col gap-3">
        {children}
      </div>

      <div ref={observerRef} className="h-1 w-full" aria-hidden="true" />

      {status === 'loading' && (
        <div className="flex items-center justify-center py-4">
          {loader ?? (
            <div className="flex items-center gap-2 text-sm text-ink-muted">
              <Spinner size="sm" tone="brand" />
              <span>در حال بارگذاری...</span>
            </div>
          )}
        </div>
      )}

      {status === 'error' && (
        <div className="flex flex-col items-center justify-center gap-2 py-4">
          <p className="text-sm text-danger">خطا در بارگذاری. لطفاً دوباره تلاش کنید.</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
            >
              تلاش مجدد
            </button>
          )}
        </div>
      )}

      {status === 'complete' && (
        <div className="flex items-center justify-center py-4">
          {endMessage ?? <p className="text-xs text-ink-muted">تمام محتوا بارگذاری شد.</p>}
        </div>
      )}
    </div>
  );
}
