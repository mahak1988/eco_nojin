import type { EChartsOption } from 'echarts';
import { buildBaseOption } from './theme';
import { EChartBase } from './EChartBase';

export type BarChartProps = {
  categories: (string | number)[];
  series: { name: string; data: number[] }[];
  horizontal?: boolean;
  stack?: boolean;
  height?: number;
  loading?: boolean;
};

export function BarChart({ categories, series, horizontal, stack, height, loading }: BarChartProps) {
  const option: EChartsOption = buildBaseOption({
    xAxis: horizontal ? { type: 'value' } : { type: 'category', data: categories.map(String) },
    yAxis: horizontal ? { type: 'category', data: categories.map(String) } : { type: 'value' },
    series: series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      stack: stack ? 'total' : undefined,
      barMaxWidth: 36,
      itemStyle: { borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
    })),
  });
  return <EChartBase option={option} height={height} loading={loading} />;
}