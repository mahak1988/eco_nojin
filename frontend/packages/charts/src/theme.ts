/**
 * Shared ECharts theme aligned with design tokens.
 * `brand` colors echo Tailwind palette so charts feel native.
 */
import type { EChartsOption } from 'echarts';

export const BRAND_PALETTE = ['#af5f1e', '#dca164', '#7b9e3b', '#3780b3', '#a3548b', '#b88436'] as const;

export const CHART_FONT = '"Inter", "Vazirmatn", system-ui, sans-serif';

export function buildBaseOption(overrides: Partial<EChartsOption> = {}): EChartsOption {
  return {
    color: [...BRAND_PALETTE],
    textStyle: { fontFamily: CHART_FONT, color: '#18181c' },
    grid: { left: 48, right: 24, top: 32, bottom: 40, containLabel: true },
    legend: { icon: 'circle', itemWidth: 10, itemHeight: 10, textStyle: { color: '#56565c' } },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(24,24,28,0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontFamily: CHART_FONT },
      padding: 10,
    },
    animationDuration: 600,
    ...overrides,
  };
}