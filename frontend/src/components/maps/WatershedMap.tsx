// frontend/src/components/maps/WatershedMap.tsx
import { useEffect, useRef } from 'react';
import { Map as MaplibreMap } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { Feature, FeatureCollection } from 'geojson';

export interface WatershedMapProps {
  watershedGeoJson?: FeatureCollection | Feature | null;
}

/**
 * Interactive watershed map built directly on MapLibre GL (open source),
 * with a GeoJSON watershed overlay (fill layer).
 */
export function WatershedMap({ watershedGeoJson }: WatershedMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MaplibreMap | null>(null);

  // Create the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new MaplibreMap({
      container: containerRef.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [51.5, 35.5],
      zoom: 12,
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Add / update the watershed GeoJSON layer when data changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !watershedGeoJson) return;
    const addWatershedLayer = () => {
      if (map.getSource('watershed')) return;
      map.addSource('watershed', { type: 'geojson', data: watershedGeoJson as GeoJSON.GeoJSON });
      map.addLayer({
        id: 'watershed-fill',
        type: 'fill',
        source: 'watershed',
        paint: { 'fill-color': '#088', 'fill-opacity': 0.3 },
      });
    };
    if (map.isStyleLoaded()) addWatershedLayer();
    else map.once('load', addWatershedLayer);
  }, [watershedGeoJson]);

  return <div ref={containerRef} style={{ width: '100%', height: '600px' }} />;
}
