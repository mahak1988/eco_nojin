/**
 * Layer Configuration
 * ===================
 * Terrain visualization layers and their properties.
 *
 * @module features/hydroma/constants
 */

import type { LayerDef } from '../types';

/**
 * Available terrain layers
 */
export const LAYERS: LayerDef[] = [
  { key: 'soil', label: 'Soil', fa: 'خاک', color: '#f59e0b' },
  { key: 'bedrock', label: 'Bedrock', fa: 'بستر', color: '#6b7280' },
  { key: 'moisture', label: 'Moisture', fa: 'رطوبت', color: '#3b82f6' },
  { key: 'roots', label: 'Roots', fa: 'ریشه', color: '#8b5cf6' },
  { key: 'groundwater', label: 'Groundwater', fa: 'آب زیرزمینی', color: '#0ea5e9' },
  { key: 'ndvi', label: 'NDVI', fa: 'پوشش گیاهی', color: '#22c55e' },
] as const;

/**
 * Default layer visibility
 */
export const DEFAULT_LAYER_VISIBILITY = {
  soil: false,
  bedrock: false,
  moisture: false,
  roots: false,
  groundwater: false,
  ndvi: false,
} as const;
