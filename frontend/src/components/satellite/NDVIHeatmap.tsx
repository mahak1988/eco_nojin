// frontend/src/components/satellite/NDVIHeatmap.tsx
import DeckGL from '@deck.gl/react';
import { HexagonLayer } from '@deck.gl/aggregation-layers';

export interface NDVIHeatmapProps {
  satellitePoints: Array<{ longitude: number; latitude: number; ndvi?: number }>;
}

export function NDVIHeatmap({ satellitePoints }: NDVIHeatmapProps) {
  const layer = new HexagonLayer({
    id: 'ndvi-hexagon',
    data: satellitePoints,
    extruded: true,
    radius: 200,
    elevationScale: 100,
    getPosition: (d: any) => [d.longitude, d.latitude],
    getWeight: (d: any) => d.ndvi,
    colorRange: [
      [255, 255, 178], // زرد - خاک برهنه
      [254, 204, 92],
      [253, 141, 60],
      [227, 74, 51],
      [179, 0, 0], // قرمز - پوشش ضعیف
      [0, 128, 0], // سبز - پوشش سالم
    ],
  });

  return <DeckGL layers={[layer]} />;
}
