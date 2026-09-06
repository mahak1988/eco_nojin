import type { EChartsOption } from 'echarts';
import { buildBaseOption } from './theme';
import { EChartBase } from './EChartBase';

export type AreaChartProps = {
  categories: (string | number)[];
  series: { name: string; data: number[] }[];
  stack?: boolean;
  height?: number;
  loading?: boolean;
};

export function AreaChart({ categories, series, stack, height, loading }: AreaChartProps) {
  const option: EChartsOption = buildBaseOption({
    xAxis: { type: 'category', data: categories.map(String), boundaryGap: false },
    yAxis: { type: 'value' },
    series: series.map((s) => ({
      name: s.name,
      type: 'line',
      stack: stack ? 'total' : undefined,
      smooth: true,
      areaStyle: { opacity: 0.32 },
      data: s.data,
      showSymbol: categories.length < 60,
    })),
  });
  return <EChartBase option={option} height={height} loading={loading} />;
}