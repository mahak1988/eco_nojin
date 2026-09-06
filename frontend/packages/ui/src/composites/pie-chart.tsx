import { EChartBase } from '@eco/charts'
import { cn } from '@eco/utils'
import { useMemo } from 'react'

export type PieChartProps = {
  data: { name: string; value: number }[]
  title?: string
  height?: number
  className?: string
}

export function PieChart({ data, title, height = 320, className }: PieChartProps) {
  const option = useMemo(
    () => ({
      title: title
        ? { text: title, left: 'center', textStyle: { fontSize: 14, fontWeight: 'bold' as const } }
        : undefined,
      tooltip: { trigger: 'item' as const },
      legend: { orient: 'vertical' as const, left: 'left', textStyle: { fontSize: 12 } },
      series: [
        {
          type: 'pie' as const,
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { show: true, fontSize: 12 },
          data,
        },
      ],
    }),
    [data, title],
  )

  return <EChartBase option={option} height={height} className={cn('w-full', className)} />
}
