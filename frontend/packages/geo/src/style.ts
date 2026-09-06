import type { StyleSpecification } from 'maplibre-gl';

/**
 * Open-source map style defaults.
 * Apps should prefer passing `VITE_MAP_STYLE_URL` at build time.
 */
export const OPENFREEMAP_LIBERTY =
  'https://tiles.openfreemap.org/styles/liberty' as const;

export const OPENFREEMAP_BRIGHT =
  'https://tiles.openfreemap.org/styles/bright' as const;

export const ECOSOIL_STYLE: StyleSpecification = {
  version: 8,
  name: 'EcoSoil',
  glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
  sources: {
    ecoregions: {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] },
    },
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: { 'background-color': '#f6f4f0' },
    },
  ],
};