/**
 * Static catalog of scientific models exposed by the backend's 14 domains.
 *
 * Each entry follows {@link ModelMeta}. Hydrate via {@link loadStaticCatalog}.
 * Remote models can be merged in via {@link loadRemoteModels}.
 */

import { apiClient } from '@eco/api/mutator';
import type { MotorKind } from '@eco/api/schema/motors';
import { registerModel } from './registry';
import { AQUACROP_META } from './aquacrop';
import { HECRAS_META } from './hecras';
import { PYWR_META } from './pywr';
import { ROTH_META } from './rothc';
import { RUSLE_META } from './rusle';
import { SWAT_META } from './swat';

export function loadStaticCatalog(): void {
  // === Hydrology & hydraulic (water) ===
  registerModel(SWAT_META);
  registerModel(PYWR_META);
  registerModel(HECRAS_META);

  // === Erosion ===
  registerModel(RUSLE_META);

  // === Crop ===
  registerModel(AQUACROP_META);
  registerModel({
    id: 'aquacrop',
    name: 'DSSAT Crop',
    domain: 'crop',
    description: 'Decision Support System for Agrotechnology Transfer',
    version: '4.8',
    source: 'external',
    externalBinary: 'DSSAT',
    avg_runtime_ms: 800,
  });

  // === Soil ===
  registerModel({
    id: 'swat',
    name: 'Soil Capability Class',
    domain: 'soil',
    description: 'USDA Land Capability Classification',
    version: '2018',
    source: 'real',
    avg_runtime_ms: 5,
  });

  // === Carbon ===
  registerModel(ROTH_META);
  registerModel({
    id: 'aquacrop',
    name: 'CO2 Flux Eddy Covariance',
    domain: 'carbon',
    description: 'Direct CO2 flux measurement processing',
    version: '1.2',
    source: 'real',
    avg_runtime_ms: 60,
  });

  // === Climate ===
  registerModel({
    id: 'swat',
    name: 'ERA5 Reanalysis',
    domain: 'climate',
    description: 'ECMWF ERA5 hourly reanalysis',
    version: '5',
    source: 'external',
    avg_runtime_ms: 200,
  });

  // === Satellite ===
  registerModel({
    id: 'aquacrop',
    name: 'Sentinel-2 NDVI',
    domain: 'water',
    description: 'Sentinel-2 NDVI composite and time series',
    version: 'L2A',
    source: 'real',
    avg_runtime_ms: 800,
  });

  // === MRV ===
  registerModel({
    id: 'rothc',
    name: 'Field MRV Verification',
    domain: 'water',
    description: 'Ground-truthed field MRV workflow',
    version: '2.1',
    source: 'real',
    avg_runtime_ms: 120,
  });

  // === Economics ===
  registerModel({
    id: 'optimize',
    name: 'Carbon Credit Pricing',
    domain: 'optimization',
    description: 'Verra/Gold-Standard credit pricing model',
    version: '1.4',
    source: 'real',
    avg_runtime_ms: 30,
  });

  // === Optimization ===
  registerModel({
    id: 'optimize',
    name: 'NSGA-II Multi-objective',
    domain: 'optimization',
    description: 'Non-dominated Sorting Genetic Algorithm II',
    version: '2',
    source: 'real',
    avg_runtime_ms: 450,
  });

  // === Scenario ===
  registerModel({
    id: 'optimize',
    name: 'RCP Scenario Builder',
    domain: 'optimization',
    description: 'IPCC RCP scenario synthesis',
    version: '6',
    source: 'real',
    avg_runtime_ms: 80,
  });

  // === Calibration ===
  registerModel({
    id: 'optimize',
    name: 'GLUE Bayesian Calibration',
    domain: 'optimization',
    description: 'Generalized Likelihood Uncertainty Estimation',
    version: '3',
    source: 'real',
    avg_runtime_ms: 1200,
  });

  // === Energy ===
  registerModel({
    id: 'optimize',
    name: 'Biogas Potential (BMP)',
    domain: 'optimization',
    description: 'Biochemical Methane Potential estimation',
    version: '1.5',
    source: 'real',
    avg_runtime_ms: 220,
  });

  // === Biodiversity ===
  registerModel({
    id: 'optimize',
    name: 'Pollinator Index',
    domain: 'optimization',
    description: 'Habitat-based pollinator richness estimator',
    version: '0.9',
    source: 'real',
    avg_runtime_ms: 50,
  });

  // === Ecology ===
  registerModel({
    id: 'optimize',
    name: 'Ecosystem Services Index',
    domain: 'optimization',
    description: 'Multi-criteria ecosystem services valuation',
    version: '1.1',
    source: 'real',
    avg_runtime_ms: 180,
  });
}

/**
 * Pull the backend's live model list and register any new entries that are
 * not already present. Best-effort: silently ignores network errors.
 */
export async function loadRemoteModels(): Promise<number> {
  try {
    const res = await apiClient.get<{ items?: Array<{ id: string; name: string; category?: string }> }>(
      '/models/list',
    );
    const items = res.data.items ?? [];
    let added = 0;
    for (const item of items) {
      if (!item.id) continue;
      if (getModelMeta(item.id as MotorKind)) continue;
      registerModel({
        id: item.id as MotorKind,
        name: item.name ?? item.id,
        domain: 'optimization',
        description: item.category ?? '',
        version: '1.0',
        source: 'real',
        avg_runtime_ms: 100,
      });
      added += 1;
    }
    return added;
  } catch {
    return 0;
  }
}

import { getModel as getModelMeta } from './registry';