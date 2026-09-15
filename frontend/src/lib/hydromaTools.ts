/** Registry-id -> engine-API mapping for every HyDroMa tool namespace.
 * Each mapped id makes its dashboard model page live through IndexRunner. */

import { HYGROMA_INDEX_IDS, hydromaIndicesApi } from './hydromaIndices';
import { makeEngineClient, type EngineApiClient } from './hydromaEngine';
import { SOIL_MODEL_IDS, hydromaSoilApi } from './hydromaSoil';

export const hydromaClimateApi = makeEngineClient('/api/v1/hydroma/climate');
export const hydromaCarbonApi = makeEngineClient('/api/v1/hydroma/carbon');
export const hydromaEconomicsApi = makeEngineClient('/api/v1/hydroma/economics');
export const hydromaSimulationApi = makeEngineClient('/api/v1/hydroma/simulation');
export const hydromaMrvApi = makeEngineClient('/api/v1/hydroma/mrv');
export const hydromaWaterApi = makeEngineClient('/api/v1/hydroma/water');

const TOOL_APIS: Record<string, EngineApiClient> = {
  // composite indices (8 live HyDroMa index models)
  ...Object.fromEntries(HYGROMA_INDEX_IDS.map((id) => [id, hydromaIndicesApi])),
  // soil science (9 tools)
  ...Object.fromEntries(SOIL_MODEL_IDS.map((id) => [id, hydromaSoilApi])),
  // climate
  'irrigation-scheduler': hydromaClimateApi,
  // carbon
  'carbon-calculator': hydromaCarbonApi,
  // economics
  'econ-analysis': hydromaEconomicsApi,
  'econ-costing': hydromaEconomicsApi,
  'econ-revenue': hydromaEconomicsApi,
  'econ-roi': hydromaEconomicsApi,
  'econ-employment': hydromaEconomicsApi,
  'econ-risk': hydromaEconomicsApi,
  // water
  'runoff-model': hydromaWaterApi,
  'runoff-surface': hydromaWaterApi,
  'groundwater-model': hydromaWaterApi,
  // mrv (pure QA/metrics tools)
  'mrv-qa': hydromaMrvApi,
  'mrv-metrics': hydromaMrvApi,
  // simulation extras
  'sim-scenarios': hydromaSimulationApi,
  // water/climate extras
  'groundwater-service': hydromaWaterApi,
  'weather-source': hydromaClimateApi,
  // simulation
  'sim-calibration': hydromaSimulationApi,
};

/** Returns the engine API client backing a registry id, or null. */
export function engineClientFor(id: string): EngineApiClient | null {
  return TOOL_APIS[id] ?? null;
}
