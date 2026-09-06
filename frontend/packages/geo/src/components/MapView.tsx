/**
 * MapView — a thin React wrapper around react-map-gl/maplibre.
 *
 * Uses OpenFreeMap (no API key required) by default. Override via
 * `VITE_MAP_STYLE_URL` to swap to a custom tile server.
 */
import type { ReactNode } from 'react';
import Map, {
  NavigationControl,
  ScaleControl,
  type MapRef,
} from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const FALLBACK_STYLE = 'https://tiles.openfreemap.org/styles/liberty';

export interface MapViewProps {
  initialLatitude?: number;
  initialLongitude?: number;
  initialZoom?: number;
  height?: number | string;
  mapStyleUrl?: string;
  children?: ReactNode;
  className?: string;
  interactive?: boolean;
}

export function MapView({
  initialLatitude = 35.6892,
  initialLongitude = 51.389,
  initialZoom = 6,
  height = 500,
  mapStyleUrl,
  children,
  className,
  interactive = true,
}: MapViewProps) {
  const styleUrl =
    mapStyleUrl ??
    (typeof import.meta !== 'undefined'
      ? (import.meta as { env?: Record<string, string | undefined> }).env?.[
          'VITE_MAP_STYLE_URL'
        ]
      : undefined) ??
    FALLBACK_STYLE;

  return (
    <div
      className={`relative w-full overflow-hidden rounded-lg border border-ink/10 ${className ?? ''}`}
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
    >
      <Map
        ref={(ref: MapRef | null) => {
          if (ref) {
            // Expose for advanced use; intentionally not part of public API
          }
        }}
        initialViewState={{
          longitude: initialLongitude,
          latitude: initialLatitude,
          zoom: initialZoom,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle={styleUrl}
        attributionControl={false}
        dragRotate={interactive}
        scrollZoom={interactive}
        doubleClickZoom={interactive}
        touchZoomRotate={interactive}
        dragPan={interactive}
      >
        <NavigationControl position="top-right" showCompass={false} />
        <ScaleControl position="bottom-left" maxWidth={120} unit="metric" />
        {children}
      </Map>
    </div>
  );
}