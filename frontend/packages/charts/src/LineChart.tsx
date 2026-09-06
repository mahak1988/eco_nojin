import type { EChartsOption } from 'echarts';
import { buildBaseOption } from './theme';
import { EChartBase } from './EChartBase';

export type SeriesPoint = { x: string | number; y: number };

export type LineSeries = {
  name: string;
  data: SeriesPoint[];
  smooth?: boolean;
  area?: boolean;
  yAxisIndex?: number;
};

export type LineChartProps = {
  series: LineSeries[];
  xLabel?: string;
  yLabel?: string;
  height?: number;
  dualAxis?: boolean;
  loading?: boolean;
};

export function LineChart({ series, xLabel, yLabel, height, dualAxis, loading }: LineChartProps) {
  const option: EChartsOption = buildBaseOption({
    grid: { left: 56, right: dualAxis ? 56 : 24, top: 32, bottom: 48, containLabel: true },
    xAxis: {
      type: 'category',
      data: series[0]?.data.map((p) => String(p.x)) ?? [],
      axisLabel: { color: '#56565c' },
      name: xLabel,
      nameLocation: 'middle',
      nameGap: 32,
    },
    yAxis: dualAxis
      ? [
          { type: 'value', name: yLabel, nameTextStyle: { color: '#56565c' } },
          { type: 'value', splitLine: { show: false } },
        ]
      : { type: 'value', name: yLabel, nameTextStyle: { color: '#56565c' } },
    series: series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: s.smooth ?? true,
      data: s.data.map((p) => p.y),
      yAxisIndex: s.yAxisIndex ?? 0,
      areaStyle: s.area ? { opacity: 0.18 } : undefined,
      showSymbol: s.data.length < 60,
    })),
  });

  return <EChartBase option={option} height={height} loading={loading} />;
}