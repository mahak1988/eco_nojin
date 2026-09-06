import type { EChartsOption } from 'echarts';
import * as echarts from 'echarts';
import { useEffect, useMemo, useRef } from 'react';
import { cn } from '@eco/utils';

export type EChartBaseProps = {
  option: EChartsOption;
  height?: number | string;
  className?: string;
  loading?: boolean;
  onClick?: (params: { name?: string; value?: unknown; seriesName?: string }) => void;
  /** Resize-observer aware. */
  autoResize?: boolean;
};

export function EChartBase({
  option,
  height = 320,
  className,
  loading,
  onClick,
  autoResize = true,
}: EChartBaseProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const c = echarts.init(ref.current, undefined, { renderer: 'canvas' });
    chartRef.current = c;

    if (onClick) {
      c.on('click', (p: { name?: string; value?: unknown; seriesName?: string }) => onClick(p));
    }

    const ro = new ResizeObserver(() => autoResize && c.resize());
    ro.observe(ref.current);

    return () => {
      ro.disconnect();
      c.dispose();
      chartRef.current = null;
    };
    // We intentionally exclude `onClick` to avoid re-init on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(option, true);
  }, [option]);

  useEffect(() => {
    if (loading) chartRef.current?.showLoading();
    else chartRef.current?.hideLoading();
  }, [loading]);

  const style = useMemo(() => ({ height, width: '100%' }), [height]);

  return <div ref={ref} className={cn('w-full', className)} style={style} />;
}