import type { CircleLayerSpecification, FillLayerSpecification, LineLayerSpecification } from 'maplibre-gl';

/**
 * Shared paint expressions used by both apps.
 */
export const SOIL_OC_FILL: FillLayerSpecification['paint'] = {
  'fill-color': [
    'interpolate',
    ['linear'],
    ['get', 'soc_pct'],
    0, '#f7e2c7',
    1, '#dca164',
    3, '#af5f1e',
    6, '#4e280d',
  ],
  'fill-opacity': 0.7,
};

export const NDVI_FILL: FillLayerSpecification['paint'] = {
  'fill-color': [
    'interpolate',
    ['linear'],
    ['get', 'ndvi'],
    0.1, '#dca164',
    0.3, '#a3b75b',
    0.5, '#5e8d3b',
    0.8, '#2d6b2b',
  ],
  'fill-opacity': 0.75,
};

export const FARM_BOUNDARY: LineLayerSpecification['paint'] = {
  'line-color': '#af5f1e',
  'line-width': 2,
  'line-dasharray': [2, 2],
};

export const FARM_CENTROID: CircleLayerSpecification['paint'] = {
  'circle-radius': 6,
  'circle-color': '#af5f1e',
  'circle-stroke-color': '#fff',
  'circle-stroke-width': 2,
};