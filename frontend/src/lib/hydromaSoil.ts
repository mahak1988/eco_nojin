/** HyDroMa soil-tools client (/api/v1/hydroma/soil) + the soil model ids
 * that map to the frontend dashboard registry entries. */

import { makeEngineClient, type EngineApiClient } from './hydromaEngine';

export const hydromaSoilApi: EngineApiClient = makeEngineClient('/api/v1/hydroma/soil');

/** Frontend registry ids backed by the HyDroMa soil engine API. */
export const SOIL_MODEL_IDS = [
  'soil-texture',
  'soil-taxonomy',
  'soil-water-retention',
  'pedotransfer',
  'soil-physics',
  'soil-chemistry',
  'soil-salinity',
  'soil-health',
  'soil-recommendations',
] as const;

export function isSoilModelId(id: string): boolean {
  return (SOIL_MODEL_IDS as readonly string[]).includes(id);
}
