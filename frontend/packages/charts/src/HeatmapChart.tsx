import type { EChartsOption } from 'echarts';
import { buildBaseOption } from './theme';
import { EChartBase } from './EChartBase';

export type HeatmapCell = { x: string | number; y: string | number; value: number };

export type HeatmapChartProps = {
  cells: HeatmapCell[];
  xLabels: (string | number)[];
  yLabels: (string | number)[];
  height?: number;
  loading?: boolean;
};

export function HeatmapChart({ cells, xLabels, yLabels, height, loading }: HeatmapChartProps) {
  const data = cells.map((c) => [xLabels.indexOf(c.x), yLabels.indexOf(c.y), c.value]);
  const values = cells.map((c) => c.value);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;

  const option: EChartsOption = buildBaseOption({
    tooltip: { position: 'top' },
    grid: { left: 80, right: 24, top: 16, bottom: 60 },
    xAxis: { type: 'category', data: xLabels.map(String), splitArea: { show: true } },
    yAxis: { type: 'category', data: yLabels.map(String), splitArea: { show: true } },
    visualMap: {
      min,
      max,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#f7e2c7', '#dca164', '#af5f1e', '#6e3812'] },
    },
    series: [{ type: 'heatmap', data, label: { show: false } }],
  });
  return <EChartBase option={option} height={height} loading={loading} />;
}