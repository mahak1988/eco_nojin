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
