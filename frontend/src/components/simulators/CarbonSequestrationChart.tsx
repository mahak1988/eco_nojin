// frontend/src/components/simulators/CarbonSequestrationChart.tsx
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';

export interface CarbonSequestrationChartProps {
  projection: { years: Array<string | number>; values: number[] };
}

export function CarbonSequestrationChart({ projection }: CarbonSequestrationChartProps) {
  const option = {
    title: {
      text: 'پیش‌بینی ترشح کربن خاک (۲۰ سال)',
      subtext: 'مدل RothC - سناریوی کشت حفاظتی' },
    xAxis: { type: 'category', data: projection.years },
    yAxis: { type: 'value', name: 'تن کربن در هکتار' },
    series: [{
      name: 'SOC (Soil Organic Carbon)',
      type: 'line',
      smooth: true,
      data: projection.values,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(76, 175, 80, 0.4)' },
          { offset: 1, color: 'rgba(76, 175, 80, 0.05)' },
        ]) } }],
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const co2e = params[0].value * 44/12;
        return `${params[0].name}<br/>
                SOC: ${params[0].value.toFixed(2)} t/ha<br/>
                CO2e: ${co2e.toFixed(2)} t<br/>
                Credits: ${(co2e * 0.85).toFixed(2)}`;
      } } };

  return <ReactEChartsCore option={option} style={{ height: 400 }} />;
}