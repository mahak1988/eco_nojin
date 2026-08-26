import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface LivestockHerdData {
  animalType: string;
  headCount: number;
  revenue: number;
  feedCost: number;
  vetCost: number;
  laborCost: number;
  netProfit: number;
}

interface LivestockEconomicsProps {
  herds: LivestockHerdData[];
}

/**
 * نمودار اقتصاد دام (هزینه/درآمد/سود)
 */
export const LivestockEconomicsChart: React.FC<LivestockEconomicsProps> = ({ herds }) => {
  const option = useMemo(() => {
    if (herds.length === 0) {
      return { title: { text: 'هیچ دامی اضافه نشده' } };
    }

    const labels = herds.map(h => `${h.animalType} (${h.headCount} رأس)`);

    return {
      title: { text: 'اقتصاد گله', left: 'center' },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['درآمد', 'خوراک', 'دامپزشکی', 'کار', 'سود خالص'], top: 30 },
      grid: { top: 80, bottom: 40 },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value', name: 'USD/سال' },
      series: [
        { name: 'درآمد', type: 'bar', stack: 'total', data: herds.map(h => h.revenue), itemStyle: { color: '#52c41a' } },
        { name: 'خوراک', type: 'bar', stack: 'cost', data: herds.map(h => h.feedCost), itemStyle: { color: '#f5222d' } },
        { name: 'دامپزشکی', type: 'bar', stack: 'cost', data: herds.map(h => h.vetCost), itemStyle: { color: '#fa541c' } },
        { name: 'کار', type: 'bar', stack: 'cost', data: herds.map(h => h.laborCost), itemStyle: { color: '#faad14' } },
        { name: 'سود خالص', type: 'line', data: herds.map(h => h.netProfit), itemStyle: { color: '#722ed1' }, lineStyle: { width: 3 } },
      ] };
  }, [herds]);

  return (
    <div style={{ padding: 20, background: '#fff', borderRadius: 8 }}>
      <ReactECharts option={option} style={{ height: 400 }} />
    </div>
  );
};
