import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface CropComparisonProps {
  currentCrop?: {
    cropType: string;
    yieldTonHa: number;
    waterMm: number;
    revenue: number;
  };
  alternativeCrop?: {
    cropType: string;
    yieldTonHa: number;
    waterMm: number;
    revenue: number;
  };
}

/**
 * نمودار مقایسه دو سناریوی کشت
 */
export const CropComparisonChart: React.FC<CropComparisonProps> = ({
  currentCrop,
  alternativeCrop }) => {
  const option = useMemo(() => {
    if (!currentCrop && !alternativeCrop) {
      return { title: { text: 'هیچ سناریویی انتخاب نشده' } };
    }

    const crops = [];
    const yields = [];
    const waters = [];
    const revenues = [];

    if (currentCrop) {
      crops.push(`جاری: ${currentCrop.cropType}`);
      yields.push(currentCrop.yieldTonHa);
      waters.push(currentCrop.waterMm);
      revenues.push(currentCrop.revenue);
    }

    if (alternativeCrop) {
      crops.push(`جایگزین: ${alternativeCrop.cropType}`);
      yields.push(alternativeCrop.yieldTonHa);
      waters.push(alternativeCrop.waterMm);
      revenues.push(alternativeCrop.revenue);
    }

    return {
      title: { text: 'مقایسه سناریوهای کشت', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['عملکرد (تن/هکتار)', 'نیاز آبی (mm)', 'درآمد (USD)'], top: 30 },
      grid: { top: 80, bottom: 40 },
      xAxis: { type: 'category', data: crops },
      yAxis: [
        { type: 'value', name: 'تن/هکتار یا mm', position: 'left' },
        { type: 'value', name: 'USD', position: 'right' },
      ],
      series: [
        {
          name: 'عملکرد (تن/هکتار)',
          type: 'bar',
          data: yields,
          itemStyle: { color: '#52c41a' } },
        {
          name: 'نیاز آبی (mm)',
          type: 'bar',
          data: waters,
          itemStyle: { color: '#1890ff' } },
        {
          name: 'درآمد (USD)',
          type: 'line',
          yAxisIndex: 1,
          data: revenues,
          itemStyle: { color: '#faad14' },
          lineStyle: { width: 3 } },
      ] };
  }, [currentCrop, alternativeCrop]);

  return (
    <div style={{ padding: 20, background: '#fff', borderRadius: 8 }}>
      <ReactECharts option={option} style={{ height: 400 }} />
    </div>
  );
};
