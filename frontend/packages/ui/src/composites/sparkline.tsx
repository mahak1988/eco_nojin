import { EChartBase } from '@eco/charts'
import { cn } from '@eco/utils'
import * as echarts from 'echarts'
import { useMemo } from 'react'

export type SparklineProps = {
  data: number[]
  color?: string
  height?: number
  className?: string
}

export function Sparkline({ data, color = '#16a34a', height = 80, className }: SparklineProps) {
  const option = useMemo(
    () => ({
      grid: { top: 4, right: 4, bottom: 4, left: 4 },
      xAxis: { type: 'category' as const, show: false, data: data.map((_, i) => i) },
      yAxis: { type: 'value' as const, show: false },
      series: [
        {
          type: 'line' as const,
          data,
          smooth: true,
          symbol: 'none',
          lineStyle: { color, width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color },
              { offset: 1, color: 'transparent' },
            ]),
          },
        },
      ],
      tooltip: { trigger: 'axis' as const },
    }),
    [data, color],
  )

  return <EChartBase option={option} height={height} className={cn('w-full', className)} />
}
