import { RechartsChart } from './RechartsChart';
import type { DataPoint } from './EcoChart';

export interface NDVIChartProps {
  months: string[];
  monthsEn: string[];
  ndvi: number[];
  ndwi?: number[];
  height?: number;
}

export function NDVIChart({
  months,
  monthsEn,
  ndvi,
  ndwi,
  height = 280,
}: NDVIChartProps) {
  const data: DataPoint[] = months.map((m, i) => ({
    label: monthsEn[i] ?? m,
    value: ndvi[i] ?? 0,
    secondary: ndwi?.[i],
  }));

  return (
    <RechartsChart
      data={data}
      title="NDVI Time Series"
      color="#2fb36b"
      height={height}
    />
  );
}
