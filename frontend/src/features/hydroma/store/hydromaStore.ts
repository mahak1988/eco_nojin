/**
 * HyDroMa Zustand Store
 * ======================
 * Centralized state management for Hydrological & Topographical Modeling Center.
 *
 * This store replaces 28 useState variables from HyDroMaCenter.tsx (8804 lines)
 * with a single, type-safe, testable store.
 *
 * Architecture:
 * - Core state: terrain, viewMode, toolMode
 * - Interactions: placedOps, polygons, plots
 * - Visual: growth, crop, decor, layers
 * - Climate: wind, rain, tour
 * - DEM: loading, error, siteMeta
 * - Effects: erosion, tour
 *
 * @module features/hydroma/store
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  TerrainData,
  ViewMode,
  ToolMode,
  PlacedOp,
  Polygon,
  DataPlot,
  LayerVisibility,
  ClimateState,
  VisualState,
  SiteMeta,
  ErosionEffect,
  CropType,
} from '../types';
import { DEFAULT_LAYER_VISIBILITY } from '../constants';

// ─────────────────────────────────────────────────────────────────────
// Store Interface
// ─────────────────────────────────────────────────────────────────────

export interface HydromaStore {
  // ── Core State ──────────────────────────────────────────────────
  terrain: TerrainData | null;
  viewMode: ViewMode;
  toolMode: ToolMode;
  selectedOpType: string | null;

  // ── Interactions ────────────────────────────────────────────────
  placedOps: PlacedOp[];
  polygons: Polygon[];
  currentDrawing: Array<{ x: number; y: number }>;
  selectedOp: string | null;
  plots: DataPlot[];

  // ── Visual State ────────────────────────────────────────────────
  visual: VisualState;

  // ── Layers ──────────────────────────────────────────────────────
  layers: LayerVisibility;

  // ── Climate ─────────────────────────────────────────────────────
  climate: ClimateState;

  // ── DEM State ───────────────────────────────────────────────────
  demLoading: boolean;
  demError: string;
  siteMeta: SiteMeta | null;
  showNdvi: boolean;

  // ── Effects ─────────────────────────────────────────────────────
  erosionEffect: ErosionEffect | null;
  tourOn: boolean;

  // ── Debug ───────────────────────────────────────────────────────
  lastClickInfo: string;

  // ── Actions: Core ───────────────────────────────────────────────
  setTerrain: (terrain: TerrainData | null) => void;
  setViewMode: (mode: ViewMode) => void;
  setToolMode: (mode: ToolMode) => void;
  setSelectedOpType: (type: string | null) => void;

  // ── Actions: Placed Operations ──────────────────────────────────
  addPlacedOp: (op: PlacedOp) => void;
  removePlacedOp: (id: string) => void;
  setSelectedOp: (id: string | null) => void;
  clearPlacedOps: () => void;

  // ── Actions: Polygons ───────────────────────────────────────────
  addDrawingPoint: (point: { x: number; y: number }) => void;
  clearDrawing: () => void;
  addPolygon: (polygon: Polygon) => void;
  removePolygon: (id: string) => void;
  clearPolygons: () => void;

  // ── Actions: Plots ──────────────────────────────────────────────
  addPlot: (plot: DataPlot) => void;
  clearPlots: () => void;

  // ── Actions: Visual ─────────────────────────────────────────────
  setShowDecor: (show: boolean) => void;
  setGrowth: (growth: number) => void;
  setCropVisual: (crop: CropType) => void;

  // ── Actions: Layers ─────────────────────────────────────────────
  toggleLayer: (layer: keyof LayerVisibility) => void;
  setLayerVisibility: (layer: keyof LayerVisibility, visible: boolean) => void;
  resetLayers: () => void;

  // ── Actions: Climate ────────────────────────────────────────────
  setWindSpeed: (speed: number) => void;
  setWindDirection: (direction: number) => void;
  toggleRain: () => void;
  setRainOn: (on: boolean) => void;

  // ── Actions: DEM ────────────────────────────────────────────────
  setDemLoading: (loading: boolean) => void;
  setDemError: (error: string) => void;
  setSiteMeta: (meta: SiteMeta | null) => void;
  setShowNdvi: (show: boolean) => void;

  // ── Actions: Effects ────────────────────────────────────────────
  setErosionEffect: (effect: ErosionEffect | null) => void;
  toggleTour: () => void;
  setTourOn: (on: boolean) => void;

  // ── Actions: Debug ──────────────────────────────────────────────
  setLastClickInfo: (info: string) => void;

  // ── Actions: Reset ──────────────────────────────────────────────
  reset: () => void;
}

// ─────────────────────────────────────────────────────────────────────
// Initial State
// ─────────────────────────────────────────────────────────────────────

const initialState = {
  terrain: null,
  viewMode: '3d' as ViewMode,
  toolMode: 'orbit' as ToolMode,
  selectedOpType: null,
  placedOps: [],
  polygons: [],
  currentDrawing: [],
  selectedOp: null,
  plots: [],
  visual: {
    showDecor: true,
    growth: 0.6,
    cropVisual: 'corn' as CropType,
  },
  layers: { ...DEFAULT_LAYER_VISIBILITY },
  climate: {
    windSpeed: 15,
    windDirection: 180,
    rainOn: false,
  },
  demLoading: false,
  demError: '',
  siteMeta: null,
  showNdvi: false,
  erosionEffect: null,
  tourOn: false,
  lastClickInfo: '',
};

// ─────────────────────────────────────────────────────────────────────
// Store Implementation
// ─────────────────────────────────────────────────────────────────────

export const useHydromaStore = create<HydromaStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      ...initialState,

      // ── Core Actions ────────────────────────────────────────────
      setTerrain: (terrain) => set({ terrain }, false, 'setTerrain'),

      setViewMode: (viewMode) => set({ viewMode }, false, 'setViewMode'),

      setToolMode: (toolMode) => set({ toolMode }, false, 'setToolMode'),

      setSelectedOpType: (selectedOpType) => set({ selectedOpType }, false, 'setSelectedOpType'),

      // ── Placed Operations ───────────────────────────────────────
      addPlacedOp: (op) =>
        set((state) => ({ placedOps: [...state.placedOps, op] }), false, 'addPlacedOp'),

      removePlacedOp: (id) =>
        set(
          (state) => ({
            placedOps: state.placedOps.filter((op) => op.id !== id),
          }),
          false,
          'removePlacedOp'
        ),

      setSelectedOp: (selectedOp) => set({ selectedOp }, false, 'setSelectedOp'),

      clearPlacedOps: () => set({ placedOps: [] }, false, 'clearPlacedOps'),

      // ── Polygons ────────────────────────────────────────────────
      addDrawingPoint: (point) =>
        set(
          (state) => ({
            currentDrawing: [...state.currentDrawing, point],
          }),
          false,
          'addDrawingPoint'
        ),

      clearDrawing: () => set({ currentDrawing: [] }, false, 'clearDrawing'),

      addPolygon: (polygon) =>
        set(
          (state) => ({
            polygons: [...state.polygons, polygon],
            currentDrawing: [],
          }),
          false,
          'addPolygon'
        ),

      removePolygon: (id) =>
        set(
          (state) => ({
            polygons: state.polygons.filter((p) => p.id !== id),
          }),
          false,
          'removePolygon'
        ),

      clearPolygons: () => set({ polygons: [] }, false, 'clearPolygons'),

      // ── Plots ───────────────────────────────────────────────────
      addPlot: (plot) => set((state) => ({ plots: [...state.plots, plot] }), false, 'addPlot'),

      clearPlots: () => set({ plots: [] }, false, 'clearPlots'),

      // ── Visual ──────────────────────────────────────────────────
      setShowDecor: (showDecor) =>
        set(
          (state) => ({
            visual: { ...state.visual, showDecor },
          }),
          false,
          'setShowDecor'
        ),

      setGrowth: (growth) =>
        set(
          (state) => ({
            visual: { ...state.visual, growth },
          }),
          false,
          'setGrowth'
        ),

      setCropVisual: (cropVisual) =>
        set(
          (state) => ({
            visual: { ...state.visual, cropVisual },
          }),
          false,
          'setCropVisual'
        ),

      // ── Layers ──────────────────────────────────────────────────
      toggleLayer: (layer) =>
        set(
          (state) => ({
            layers: {
              ...state.layers,
              [layer]: !state.layers[layer],
            },
          }),
          false,
          `toggleLayer/${layer}`
        ),

      setLayerVisibility: (layer, visible) =>
        set(
          (state) => ({
            layers: {
              ...state.layers,
              [layer]: visible,
            },
          }),
          false,
          `setLayerVisibility/${layer}`
        ),

      resetLayers: () => set({ layers: { ...DEFAULT_LAYER_VISIBILITY } }, false, 'resetLayers'),

      // ── Climate ─────────────────────────────────────────────────
      setWindSpeed: (windSpeed) =>
        set(
          (state) => ({
            climate: { ...state.climate, windSpeed },
          }),
          false,
          'setWindSpeed'
        ),

      setWindDirection: (windDirection) =>
        set(
          (state) => ({
            climate: { ...state.climate, windDirection },
          }),
          false,
          'setWindDirection'
        ),

      toggleRain: () =>
        set(
          (state) => ({
            climate: {
              ...state.climate,
              rainOn: !state.climate.rainOn,
            },
          }),
          false,
          'toggleRain'
        ),

      setRainOn: (rainOn) =>
        set(
          (state) => ({
            climate: { ...state.climate, rainOn },
          }),
          false,
          'setRainOn'
        ),

      // ── DEM ─────────────────────────────────────────────────────
      setDemLoading: (demLoading) => set({ demLoading }, false, 'setDemLoading'),

      setDemError: (demError) => set({ demError }, false, 'setDemError'),

      setSiteMeta: (siteMeta) => set({ siteMeta }, false, 'setSiteMeta'),

      setShowNdvi: (showNdvi) => set({ showNdvi }, false, 'setShowNdvi'),

      // ── Effects ─────────────────────────────────────────────────
      setErosionEffect: (erosionEffect) => set({ erosionEffect }, false, 'setErosionEffect'),

      toggleTour: () => set((state) => ({ tourOn: !state.tourOn }), false, 'toggleTour'),

      setTourOn: (tourOn) => set({ tourOn }, false, 'setTourOn'),

      // ── Debug ───────────────────────────────────────────────────
      setLastClickInfo: (lastClickInfo) => set({ lastClickInfo }, false, 'setLastClickInfo'),

      // ── Reset ───────────────────────────────────────────────────
      reset: () => set(initialState, false, 'reset'),
    }),
    { name: 'HydromaStore' }
  )
);

// ─────────────────────────────────────────────────────────────────────
// Selectors (for optimized re-renders)
// ─────────────────────────────────────────────────────────────────────

/**
 * Selector for terrain data
 */
export const selectTerrain = (state: HydromaStore) => state.terrain;

/**
 * Selector for view mode
 */
export const selectViewMode = (state: HydromaStore) => state.viewMode;

/**
 * Selector for tool mode
 */
export const selectToolMode = (state: HydromaStore) => state.toolMode;

/**
 * Selector for placed operations
 */
export const selectPlacedOps = (state: HydromaStore) => state.placedOps;

/**
 * Selector for polygons
 */
export const selectPolygons = (state: HydromaStore) => state.polygons;

/**
 * Selector for layers
 */
export const selectLayers = (state: HydromaStore) => state.layers;

/**
 * Selector for climate
 */
export const selectClimate = (state: HydromaStore) => state.climate;

/**
 * Selector for visual state
 */
export const selectVisual = (state: HydromaStore) => state.visual;

/**
 * Selector for DEM state
 */
export const selectDemState = (state: HydromaStore) => ({
  loading: state.demLoading,
  error: state.demError,
  siteMeta: state.siteMeta,
});
