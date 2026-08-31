import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface WaterBudgetProps {
  precipitationMm?: number;
  infiltrationMm?: number;
  runoffMm?: number;
  evapotranspirationMm?: number;
  aquiferRechargeMm?: number;
}

/**
 * نمودار بودجه آب (Green-Ampt + SWAT+)
 */
export const WaterBudgetChart: React.FC<WaterBudgetProps> = ({
  precipitationMm = 100,
  infiltrationMm = 60,
  runoffMm = 20,
  evapotranspirationMm = 15,
  aquiferRechargeMm = 5,
}) => {
  const option = useMemo(
    () => ({
      title: { text: 'بودجه آب زمین', left: 'center' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} mm ({d}%)' },
      legend: { top: 30 },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '60%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
          label: { show: true, formatter: '{b}\n{c} mm' },
          data: [
            { value: infiltrationMm, name: 'نفوذ', itemStyle: { color: '#52c41a' } },
            { value: runoffMm, name: 'رواناب', itemStyle: { color: '#1890ff' } },
            { value: evapotranspirationMm, name: 'تبخیر-تعریق', itemStyle: { color: '#faad14' } },
            { value: aquiferRechargeMm, name: 'تغذیه آبخوان', itemStyle: { color: '#722ed1' } },
          ],
        },
      ],
    }),
    [precipitationMm, infiltrationMm, runoffMm, evapotranspirationMm, aquiferRechargeMm]
  );

  return (
    <div style={{ padding: 20, background: '#fff', borderRadius: 8 }}>
      <ReactECharts option={option} style={{ height: 400 }} />
    </div>
  );
};
