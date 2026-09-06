/**
 * GeoJsonLayer — renders any GeoJSON FeatureCollection as fill/line/circle
 * styled by the `paint` expression driven by feature properties.
 */
import { Layer, Source } from 'react-map-gl/maplibre';
import type { FeatureCollection } from 'geojson';

export type GeoJsonLayerKind = 'fill' | 'line' | 'circle';

export interface GeoJsonLayerProps {
  id: string;
  data: FeatureCollection;
  type?: GeoJsonLayerKind;
  color?: string;
  fillOpacity?: number;
}

export function GeoJsonLayer({
  id,
  data,
  type = 'fill',
  color = '#16a34a',
  fillOpacity = 0.4,
}: GeoJsonLayerProps) {
  if (type === 'fill') {
    return (
      <Source id={id} type="geojson" data={data}>
        <Layer
          id={`${id}-fill`}
          type="fill"
          paint={{
            'fill-color': color,
            'fill-opacity': fillOpacity,
          }}
        />
        <Layer
          id={`${id}-outline`}
          type="line"
          paint={{
            'line-color': color,
            'line-width': 2,
          }}
        />
      </Source>
    );
  }

  if (type === 'circle') {
    return (
      <Source id={id} type="geojson" data={data}>
        <Layer
          id={`${id}-circle`}
          type="circle"
          paint={{
            'circle-radius': 6,
            'circle-color': color,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
          }}
        />
      </Source>
    );
  }

  return (
    <Source id={id} type="geojson" data={data}>
      <Layer
        id={`${id}-line`}
        type="line"
        paint={{
          'line-color': color,
          'line-width': 3,
        }}
      />
    </Source>
  );
}