import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';

export type VirtualizedListProps<T> = {
  items: T[];
  itemHeight: number;
  overscan?: number;
  renderItem: (item: T, index: number) => ReactNode;
  className?: string;
  orientation?: 'vertical' | 'horizontal';
  onEndReached?: () => void;
  onEndReachedThreshold?: number;
};

export function VirtualizedList<T>({
  items,
  itemHeight,
  overscan = 5,
  renderItem,
  className,
  orientation = 'vertical',
  onEndReached,
  onEndReachedThreshold = 200,
}: VirtualizedListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState(0);
  const isVertical = orientation === 'vertical';

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const updateSize = () => {
      setContainerSize(isVertical ? element.clientHeight : element.clientWidth);
    };

    updateSize();
    const resizeObserver = new ResizeObserver(updateSize);
    resizeObserver.observe(element);

    return () => resizeObserver.disconnect();
  }, [isVertical]);

  const totalSize = isVertical ? items.length * itemHeight : items.length * itemHeight;
  const scrollSize = isVertical ? scrollTop : scrollLeft;
  const containerLength = containerSize;

  const startIndex = Math.max(0, Math.floor(scrollSize / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollSize + containerLength) / itemHeight) + overscan,
  );

  const visibleItems: { index: number; item: T }[] = [];
  for (let i = startIndex; i <= endIndex; i++) {
    if (i >= 0 && i < items.length) {
      const item = items[i];
      if (item !== undefined) {
        visibleItems.push({ index: i, item });
      }
    }
  }

  const handleScroll = useCallback(() => {
    const element = containerRef.current;
    if (!element) return;

    if (isVertical) {
      setScrollTop(element.scrollTop);
    } else {
      setScrollLeft(element.scrollLeft);
    }
  }, [isVertical]);

  useEffect(() => {
    if (!onEndReached) return;

    const element = containerRef.current;
    if (!element) return;

    const scrollPosition = isVertical ? element.scrollTop + element.clientHeight : element.scrollLeft + element.clientWidth;
    const threshold = isVertical ? element.scrollHeight : element.scrollWidth;

    if (scrollPosition >= threshold - onEndReachedThreshold) {
      onEndReached();
    }
  }, [scrollTop, scrollLeft, containerSize, onEndReached, onEndReachedThreshold, isVertical]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className={cn(
        'overflow-auto',
        isVertical ? 'h-full w-full' : 'h-full w-full overflow-x-auto overflow-y-hidden',
        className,
      )}
      role="list"
      aria-label="Virtualized list"
    >
      <div
        className={cn('relative', isVertical ? 'h-full' : 'h-full')}
        style={{
          [isVertical ? 'height' : 'width']: `${totalSize}px`,
        }}
      >
        {visibleItems.map(({ index, item }) => (
          <div
            key={index}
            role="listitem"
            aria-setsize={items.length}
            aria-posinset={index + 1}
            className={cn('absolute', isVertical ? 'left-0 right-0' : 'top-0 bottom-0')}
            style={{
              [isVertical ? 'top' : 'left']: `${index * itemHeight}px`,
              [isVertical ? 'height' : 'width']: `${itemHeight}px`,
            }}
          >
            {renderItem(item, index)}
          </div>
        ))}
      </div>
    </div>
  );
}
