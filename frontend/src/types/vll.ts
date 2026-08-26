/**
 * Eco Nojin - Virtual Land Laboratory Types
 * تعاریف کامل تایپ برای آزمایشگاه مجازی زمین
 */

// ─── Land & Terrain ─────────────────────────────
export interface LandCoordinate {
  lat: number;
  lng: number;
}

export interface LandBBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface SoilProfile {
  texture: 'sand' | 'loam' | 'clay' | 'silt_loam' | 'sandy_loam' | 'clay_loam';
  organicCarbonPct: number;
  ph: number;
  depthCm: number;
  bulkDensity: number;
  infiltrationRateMmHr: number;
}

export interface ClimateData {
  annualRainfallMm: number;
  avgTempC: number;
  maxTempC: number;
  minTempC: number;
  windSpeedMs: number;
  windDirectionDeg: number;
  solarRadiationMjM2: number;
  evapotranspirationMm: number;
}

export interface Topography {
  slopePct: number;
  aspectDeg: number;
  elevationM: number;
  curvature: 'concave' | 'convex' | 'flat';
}

export interface LandProfile {
  id: string;
  name: string;
  bbox: LandBBox;
  areaHa: number;
  soil: SoilProfile;
  climate: ClimateData;
  topography: Topography;
  currentLandUse: 'bare' | 'cropland' | 'rangeland' | 'forest' | 'orchard';
  ndvi: number;
  satelliteImageUrl?: string;
  demData?: number[][];
}

// ─── Interventions (مداخلات) ─────────────────────────────
export type InterventionCategory = 
  | 'biological'
  | 'engineering'
  | 'agronomic'
  | 'water_management'
  | 'livestock'
  | 'integrated';

export interface Intervention {
  id: string;
  name: string;
  nameFa: string;
  category: InterventionCategory;
  description: string;
  icon: string;
  color: string;
  parameters: InterventionParameter[];
  scientificModel: string;
  estimatedCostUsd: number;
  timeToEffectYears: number;
}

export interface InterventionParameter {
  key: string;
  label: string;
  labelFa: string;
  type: 'number' | 'select' | 'boolean';
  min?: number;
  max?: number;
  step?: number;
  defaultValue: any;
  unit?: string;
  options?: { value: string; label: string }[];
}

export interface AppliedIntervention {
  interventionId: string;
  parameters: Record<string, any>;
  appliedAt: string;
  coveragePct: number;
}

// ─── Simulation Results ─────────────────────────────
export interface HydrologyResult {
  precipitationMm: number;
  infiltrationMm: number;
  runoffMm: number;
  evapotranspirationMm: number;
  aquiferRechargeMm: number;
  peakFlowM3S: number;
}

export interface ErosionResult {
  waterErosionTonHaYear: number;
  windErosionTonHaYear: number;
  soilLossReductionPct: number;
  riskLevel: 'low' | 'moderate' | 'high' | 'severe';
}

export interface CarbonResult {
  soilCarbonTonHa: number;
  biomassCarbonTonHa: number;
  totalSequestrationTonCO2Year: number;
  creditsEarned: number;
  creditsValueUsd: number;
}

export interface CropResult {
  cropType: string;
  yieldTonHa: number;
  biomassTonHa: number;
  waterUseMm: number;
  wueKgM3: number;
  revenueUsd: number;
}

export interface LivestockResult {
  totalHead: number;
  carryingCapacity: number;
  overgrazingRisk: 'none' | 'low' | 'moderate' | 'high';
  manureTonYear: number;
  revenueUsd: number;
}

export interface EconomicsResult {
  totalCostUsd: number;
  totalRevenueUsd: number;
  netProfitUsd: number;
  npvUsd: number;
  irrPct: number;
  paybackYears: number;
  roiPct: number;
}

export interface SimulationResult {
  scenarioId: string;
  scenarioName: string;
  years: number;
  hydrology: HydrologyResult;
  erosion: ErosionResult;
  carbon: CarbonResult;
  crops: CropResult[];
  livestock: LivestockResult;
  economics: EconomicsResult;
  sustainabilityScore: number;
  biodiversityIndex: number;
  warnings: string[];
  recommendations: string[];
}

// ─── Scenario ─────────────────────────────
export interface Scenario {
  id: string;
  name: string;
  landProfile: LandProfile;
  interventions: AppliedIntervention[];
  result?: SimulationResult;
  createdAt: string;
  isBaseline: boolean;
}

// ─── AI Advisor ─────────────────────────────
export interface AdvisorMessage {
  id: string;
  role: 'user' | 'advisor';
  content: string;
  timestamp: string;
  suggestions?: string[];
}

// ─── Real Land (Phase 1 — داده واقعی) ─────────────────────────────
export type DataStatus = 'ok' | 'error' | 'no_scene' | 'band_error' | 'credentials_required' | 'not_configured';

export interface NdviGridPoint {
  lon: number;
  lat: number;
  ndvi: number;
}

export interface RealSatelliteBlock {
  status: DataStatus | string;
  data_source?: string;
  ndvi?: number | null;
  evi?: number | null;
  savi?: number | null;
  lai?: number | null;
  c_factor?: number | null;
  ndvi_grid?: NdviGridPoint[];
  scene_id?: string | null;
  sensed_at?: string | null;
  cloud_cover?: number | null;
  sensor?: string;
  lst_c?: number | null;
  lst_status?: string;
  lst_source?: string;
  s1_status?: string;
  s1_vh_vv_ratio?: number | null;
  s1_data_quality?: string;
  message?: string;
  free_registration?: string;
  error?: string;
}

export interface RealClimateBlock {
  status: DataStatus | string;
  data_source?: string;
  period?: string;
  days?: number;
  annual_rainfall_mm?: number;
  avg_temp_c?: number;
  max_temp_c?: number;
  min_temp_c?: number;
  annual_et0_mm?: number;
  monthly?: {
    precip_mm?: number[];
    tmax_c?: number[];
    tmin_c?: number[];
  };
  latest?: {
    date?: string | null;
    precipitation_mm?: number | null;
    tmax_c?: number | null;
    tmin_c?: number | null;
    et0_mm?: number | null;
  } | null;
  reference?: string;
  error?: string;
}

export interface RealSoilBlock {
  status: DataStatus | string;
  data_source?: string;
  texture?: SoilProfile['texture'] | string;
  texture_approx?: boolean;
  sand_pct?: number;
  silt_pct?: number;
  clay_pct?: number;
  soc_g_kg?: number | null;
  soc_pct?: number | null;
  ph_h2o?: number | null;
  cec_mmolc_kg?: number | null;
  bulk_density_g_cm3?: number | null;
  k_factor_rusle?: number;
  depth_layer?: string;
  sample_offset_km?: number;
  reference?: string;
  error?: string;
}

export interface RealLandSummary {
  satellite: string;
  climate: string;
  soil: string;
  all_real: boolean;
  sources: {
    satellite: string;
    climate: string;
    soil: string;
  };
}

export interface RealLandResult {
  lat: number;
  lon: number;
  analysis_date?: string | null;
  satellite: RealSatelliteBlock;
  climate: RealClimateBlock;
  soil: RealSoilBlock;
  summary: RealLandSummary;
}

// ─── Scientific Chain (Phase 2 — زنجیره علمی واقعی) ──────────────────
export interface ScientificChainResult {
  chain_id: string;
  cache_hit: boolean;
  status: string;
  location: { lat: number; lon: number };
  inputs: Record<string, unknown>;
  erosion: {
    soil_loss_ton_ha_yr?: number;
    risk?: string;
    r_factor?: number;
    k_factor?: number;
    ls_factor?: number;
    c_factor?: number;
    p_factor?: number;
  };
  swat: MotorBlock;
  water: MotorBlock;
  flood: MotorBlock;
  optimization: MotorBlock;
  rothc: MotorBlock;
  aquacrop: MotorBlock & {
    outputs?: { harvest_date?: string; yield_ton_ha?: number };
  };
  calibration: Record<string, unknown>;
  data_sources: Record<string, string>;
  error?: string | null;
}

export interface MotorBlock {
  status?: string;
  summary?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  execution_time_seconds?: number;
  error?: string | null;
}
