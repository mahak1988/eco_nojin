import type { EChartsOption } from 'echarts';
import { buildBaseOption } from './theme';
import { EChartBase } from './EChartBase';

export type GaugeChartProps = {
  value: number;
  min?: number;
  max?: number;
  unit?: string;
  thresholds?: Array<{ value: number; color: string }>;
  height?: number;
  loading?: boolean;
};

export function GaugeChart({
  value,
  min = 0,
  max = 100,
  unit,
  thresholds,
  height,
  loading,
}: GaugeChartProps) {
  const option: EChartsOption = buildBaseOption({
    series: [
      {
        type: 'gauge',
        min,
        max,
        progress: { show: true, width: 14 },
        axisLine: {
          lineStyle: {
            width: 14,
            color: thresholds
              ? thresholds.map((t) => [t.value / max, t.color])
              : [[1, '#af5f1e']],
          },
        },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: { valueAnimation: true, formatter: unit ? `{value} ${unit}` : '{value}', color: '#18181c' },
        data: [{ value }],
      },
    ],
  });
  return <EChartBase option={option} height={height ?? 220} loading={loading} />;
}