/**
 * HyDroMa Types
 * ===============
 * Type definitions for Hydrological & Topographical Modeling Center.
 *
 * This file contains all interfaces and types used in the hydroma feature.
 * Extracted from HyDroMaCenter.tsx (8804 lines) for better maintainability.
 *
 * @module features/hydroma/types
 */

// ─────────────────────────────────────────────────────────────────────
// Core Enums & Unions
// ─────────────────────────────────────────────────────────────────────

/**
 * View modes for the 3D terrain visualization
 */
export type ViewMode = '3d' | '2d-top' | '2d-side' | 'cross-section';

/**
 * Tool modes for user interaction
 */
export type ToolMode = 'orbit' | 'draw-polygon' | 'place-op' | 'data-plot';

/**
 * Layer types for terrain visualization
 */
export type LayerType =
  'surface' | 'soil' | 'bedrock' | 'ndvi' | 'moisture' | 'roots' | 'groundwater';

/**
 * Crop types for visualization
 */
export type CropType = 'corn' | 'wheat' | 'alfalfa';

// ─────────────────────────────────────────────────────────────────────
// Terrain & DEM
// ─────────────────────────────────────────────────────────────────────

/**
 * Terrain data structure
 * Imported from lib/terrainGenerator
 */
export interface TerrainData {
  width: number;
  height: number;
  elevation: number[][];
  moisture: number[][];
  minElevation: number;
  maxElevation: number;
  rootDepth?: number[][];
  groundwater?: number[][];
  erosion?: number[][];
}

/**
 * DEM (Digital Elevation Model) grid from API
 * Imported from lib/demApi
 */
export interface DemGrid {
  site_id: string;
  lat: number;
  lon: number;
  width: number;
  height: number;
  elevation: number[][];
  min_elev: number;
  max_elev: number;
}

/**
 * Site metadata
 */
export interface SiteMeta {
  lat: number;
  lon: number;
  siteId: string;
}

// ─────────────────────────────────────────────────────────────────────
// User Interactions
// ─────────────────────────────────────────────────────────────────────

/**
 * Placed engineering operation (e.g., gabion wall, check dam)
 */
export interface PlacedOp {
  id: string;
  type: string;
  x: number;
  y: number;
  label: string;
}

/**
 * Polygon drawn by user
 */
export interface Polygon {
  id: string;
  points: Array<{ x: number; y: number }>;
  name: string;
  color: string;
  area?: number;
}

/**
 * Data plot on terrain
 * Imported from components/farmsim/SceneExtras
 */
export interface DataPlot {
  id: string;
  center: [number, number];
  size: [number, number];
  data: {
    moisture: number;
    ndvi: number;
    elevation: number;
  };
}

// ─────────────────────────────────────────────────────────────────────
// Engineering Operations
// ─────────────────────────────────────────────────────────────────────

/**
 * Engineering operation definition
 */
export interface EngineeringOp {
  id: string;
  name: string;
  fa: string;
  emoji: string;
  cost: number;
}

/**
 * Erosion effect calculation result (RUSLE)
 */
export interface ErosionEffect {
  op_type: string;
  op_fa: string;
  A_before_t_ha_yr: number;
  A_after_t_ha_yr: number;
  reduction_pct: number;
  note_fa: string;
}

// ─────────────────────────────────────────────────────────────────────
// UI State
// ─────────────────────────────────────────────────────────────────────

/**
 * Layer visibility state
 */
export interface LayerVisibility {
  soil: boolean;
  bedrock: boolean;
  moisture: boolean;
  roots: boolean;
  groundwater: boolean;
  ndvi: boolean;
}

/**
 * Climate state
 */
export interface ClimateState {
  windSpeed: number;
  windDirection: number;
  rainOn: boolean;
}

/**
 * Visual state
 */
export interface VisualState {
  showDecor: boolean;
  growth: number;
  cropVisual: CropType;
}

// ─────────────────────────────────────────────────────────────────────
// Store State (for Zustand)
// ─────────────────────────────────────────────────────────────────────

/**
 * Complete hydroma store state
 * Will be used in hydromaStore.ts
 */
export interface HydromaState {
  // Core
  terrain: TerrainData | null;
  viewMode: ViewMode;
  toolMode: ToolMode;
  selectedOpType: string | null;

  // Placed items
  placedOps: PlacedOp[];
  polygons: Polygon[];
  currentDrawing: Array<{ x: number; y: number }>;
  selectedOp: string | null;
  plots: DataPlot[];

  // Visual
  visual: VisualState;

  // Layers
  layers: LayerVisibility;

  // Climate
  climate: ClimateState;

  // DEM
  demLoading: boolean;
  demError: string;
  siteMeta: SiteMeta | null;
  esriTexture: any; // THREE.Texture
  showNdvi: boolean;

  // Effects
  erosionEffect: ErosionEffect | null;
  tourOn: boolean;

  // Debug
  lastClickInfo: string;

  // Actions
  setTerrain: (terrain: TerrainData | null) => void;
  setViewMode: (mode: ViewMode) => void;
  setToolMode: (mode: ToolMode) => void;
  setSelectedOpType: (type: string | null) => void;
  addPlacedOp: (op: PlacedOp) => void;
  removePlacedOp: (id: string) => void;
  addPolygon: (polygon: Polygon) => void;
  removePolygon: (id: string) => void;
  setCurrentDrawing: (points: Array<{ x: number; y: number }>) => void;
  addPlot: (plot: DataPlot) => void;
  clearPlots: () => void;
  setLayerVisibility: (layer: keyof LayerVisibility, visible: boolean) => void;
  setWindSpeed: (speed: number) => void;
  setWindDirection: (direction: number) => void;
  setRainOn: (on: boolean) => void;
  setTourOn: (on: boolean) => void;
  setGrowth: (growth: number) => void;
  setCropVisual: (crop: CropType) => void;
  setShowDecor: (show: boolean) => void;
  reset: () => void;
}

// ─────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────

/**
 * View mode definitions
 */
export interface ViewModeDef {
  id: ViewMode;
  label: string;
  fa: string;
}

/**
 * Tool mode definitions
 */
export interface ToolModeDef {
  id: ToolMode;
  label: string;
  fa: string;
  icon: string;
  color: string;
}

/**
 * Layer definition
 */
export interface LayerDef {
  key: keyof LayerVisibility;
  label: string;
  fa: string;
  color: string;
}
