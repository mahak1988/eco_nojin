import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface CarbonForecastProps {
  years?: number;
  initialSOC?: number;
  managementScenario?: 'conventional' | 'conservation' | 'regenerative';
}

/**
 * پیش‌بینی ترشح کربن خاک (RothC)
 */
export const CarbonForecastChart: React.FC<CarbonForecastProps> = ({
  years = 20,
  initialSOC = 1.5,
  managementScenario = 'conservation' }) => {
  const option = useMemo(() => {
    const growthRates = {
      conventional: 0.005,
      conservation: 0.025,
      regenerative: 0.045 };

    const scenarios = Object.entries(growthRates).map(([name, rate]) => {
      const data = [];
      let soc = initialSOC;
      for (let y = 0; y <= years; y++) {
        data.push([y, parseFloat(soc.toFixed(3))]);
        soc = soc * (1 + rate);
      }
      return {
        name: name === 'conventional' ? 'متعارف' :
              name === 'conservation' ? 'حفاظتی' : 'بازآفرین',
        type: 'line',
        smooth: true,
        data,
        areaStyle: { opacity: 0.15 } };
    });

    return {
      title: {
        text: 'پیش‌بینی ترشح کربن خاک (۲۰ سال)',
        subtext: 'مدل RothC',
        left: 'center' },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let text = `سال ${params[0].value[0]}<br/>`;
          params.forEach((p: any) => {
            const co2e = p.value[1] * 44 / 12;
            text += `${p.marker} ${p.seriesName}: ${p.value[1].toFixed(2)} t C/ha (${co2e.toFixed(2)} t CO2e)<br/>`;
          });
          return text;
        } },
      legend: { top: 50 },
      grid: { top: 90, bottom: 40 },
      xAxis: { type: 'value', name: 'سال', min: 0, max: years },
      yAxis: { type: 'value', name: 'کربن آلی خاک (t/ha)' },
      series: scenarios };
  }, [years, initialSOC, managementScenario]);

  return (
    <div style={{ padding: 20, background: '#fff', borderRadius: 8 }}>
      <ReactECharts option={option} style={{ height: 450 }} />
    </div>
  );
};
