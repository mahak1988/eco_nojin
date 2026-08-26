import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface ErosionRiskProps {
  windErosion?: { erosionTonHaYear: number; riskLevel: string };
  waterErosion?: { soilLossTonHaYear: number; riskLevel: string };
  hasWindbreak?: boolean;
  windbreakReduction?: number;
}

/**
 * نمودار ریسک فرسایش بادی و آبی
 */
export const ErosionRiskMap: React.FC<ErosionRiskProps> = ({
  windErosion,
  waterErosion,
  hasWindbreak,
  windbreakReduction }) => {
  const option = useMemo(() => {
    const categories = ['فرسایش بادی', 'فرسایش آبی'];
    const values = [
      windErosion?.erosionTonHaYear ?? 0,
      waterErosion?.soilLossTonHaYear ?? 0,
    ];

    const colorByRisk = (risk: string) => {
      switch (risk) {
        case 'low': return '#52c41a';
        case 'moderate': return '#faad14';
        case 'high': return '#fa541c';
        case 'severe': return '#f5222d';
        default: return '#999';
      }
    };

    return {
      title: {
        text: 'تحلیل ریسک فرسایش',
        subtext: hasWindbreak ? `بادشکن فعال - کاهش ${((1 - (windbreakReduction ?? 1)) * 100).toFixed(0)}%` : 'بدون بادشکن',
        left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { top: 80, bottom: 40 },
      xAxis: { type: 'category', data: categories },
      yAxis: { type: 'value', name: 'تن در هکتار/سال' },
      series: [{
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: {
            color: i === 0
              ? colorByRisk(windErosion?.riskLevel ?? 'low')
              : colorByRisk(waterErosion?.riskLevel ?? 'low') } })),
        label: {
          show: true,
          position: 'top',
          formatter: '{c} t/ha' } }] };
  }, [windErosion, waterErosion, hasWindbreak, windbreakReduction]);

  return (
    <div style={{ padding: 20, background: '#fff', borderRadius: 8 }}>
      <ReactECharts option={option} style={{ height: 350 }} />
    </div>
  );
};
