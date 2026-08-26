import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

/**
 * تایپ‌های مشترک شبیه‌سازها
 */
export interface SimulationContext {
  villageId?: string;
  fieldId?: string;
  bbox?: { north: number; south: number; east: number; west: number };
  soil?: {
    texture: string;
    organicCarbonPct: number;
    infiltrationRateMmHr: number;
  };
  weather?: {
    precipitationMm: number;
    windSpeedMs: number;
    tempMinC: number;
    tempMaxC: number;
    solarRadiationMjM2: number;
  };
}

export interface CropPlan {
  cropType: string;
  plantingDate: string;
  areaHa: number;
}

export interface WindbreakConfig {
  treeSpecies: string;
  heightM: number;
  lengthM: number;
  porosityPct: number;
}

export interface LivestockHerd {
  animalType: 'cattle' | 'sheep' | 'goat' | 'poultry';
  headCount: number;
  productionSystem: 'grazing' | 'mixed' | 'intensive';
}

export interface SimulatorState {
  // Context
  context: SimulationContext;
  setContext: (ctx: Partial<SimulationContext>) => void;

  // Crop Planning
  currentCrop: CropPlan | null;
  alternativeCrop: CropPlan | null;
  setCropPlan: (crop: CropPlan, type: 'current' | 'alternative') => void;

  // Windbreak
  windbreak: WindbreakConfig | null;
  setWindbreak: (wb: WindbreakConfig | null) => void;

  // Livestock
  herds: LivestockHerd[];
  addHerd: (herd: LivestockHerd) => void;
  removeHerd: (index: number) => void;
  updateHerd: (index: number, herd: LivestockHerd) => void;

  // Results Cache
  results: Record<string, any>;
  setResult: (key: string, value: any) => void;
  clearResults: () => void;

  // View Mode
  viewMode: '2d' | '3d' | 'satellite';
  setViewMode: (mode: '2d' | '3d' | 'satellite') => void;
}

export const useSimulatorStore = create<SimulatorState>()(
  immer((set) => ({
    context: {
      soil: {
        texture: 'loam',
        organicCarbonPct: 1.5,
        infiltrationRateMmHr: 20,
      },
      weather: {
        precipitationMm: 50,
        windSpeedMs: 12,
        tempMinC: 15,
        tempMaxC: 32,
        solarRadiationMjM2: 18,
      },
    },

    setContext: (ctx) =>
      set((state) => {
        state.context = { ...state.context, ...ctx };
      }),

    currentCrop: null,
    alternativeCrop: null,

    setCropPlan: (crop, type) =>
      set((state) => {
        if (type === 'current') state.currentCrop = crop;
        else state.alternativeCrop = crop;
      }),

    windbreak: null,
    setWindbreak: (wb) =>
      set((state) => {
        state.windbreak = wb;
      }),

    herds: [],
    addHerd: (herd) =>
      set((state) => {
        state.herds.push(herd);
      }),
    removeHerd: (index) =>
      set((state) => {
        state.herds.splice(index, 1);
      }),
    updateHerd: (index, herd) =>
      set((state) => {
        state.herds[index] = herd;
      }),

    results: {},
    setResult: (key, value) =>
      set((state) => {
        state.results[key] = value;
      }),
    clearResults: () =>
      set((state) => {
        state.results = {};
      }),

    viewMode: '2d',
    setViewMode: (mode) =>
      set((state) => {
        state.viewMode = mode;
      }),
  }))
);
