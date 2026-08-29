/**
 * SimulationPipeline Context
 * Global state for sharing data between simulators
 * Each simulator can publish its results, and Visualization3D consumes them
 */

import { createContext, useContext, useState, ReactNode } from 'react';

export interface LandProfile {
  id: string;
  name: string;
  lat: number;
  lon: number;
  area_ha: number;
  elevation?: number[][];
  minElevation?: number;
  maxElevation?: number;
}

export interface CapabilityResult {
  landProfileId: string;
  classNumber: number;
  className: string;
  classColor: string;
  limitations: string[];
  suitableUses: string[];
  scores: {
    slope: number;
    soil: number;
    water: number;
    erosion: number;
  };
}

export interface WatershedResult {
  landProfileId: string;
  runoffDepth: number;
  peakDischarge: number;
  timeToPeak: number;
  floodWave: Array<{ time: number; flow: number }>;
  floodZones?: Array<{ x: number; y: number; depth: number }>;
}

export interface SWATResult {
  landProfileId: string;
  soilMoisture?: number[][];  // 2D grid
  evapotranspiration: number;
  waterBalance: {
    rainfall: number;
    runoff: number;
    infiltration: number;
  };
}

export interface RothCResult {
  landProfileId: string;
  carbonStock: number;        // t/ha
  carbonMap?: number[][];     // 2D grid
  carbonChange: number;       // t/ha/year
  pools: {
    DPM: number;
    RPM: number;
    BIO: number;
    HUM: number;
    IOM: number;
  };
}

export interface SatelliteData {
  landProfileId: string;
  ndvi?: number[][];          // Normalized Difference Vegetation Index
  lst?: number[][];           // Land Surface Temperature
  soilMoisture?: number[][];  // Soil Moisture
  timestamp: string;
}

export interface PipelineState {
  currentProfile: LandProfile | null;
  capability: CapabilityResult | null;
  watershed: WatershedResult | null;
  swat: SWATResult | null;
  rothc: RothCResult | null;
  satellite: SatelliteData | null;
  apiResults: Record<string, any>;
  history: Array<{
    timestamp: string;
    type: string;
    data: any;
  }>;
}

interface PipelineContextType {
  state: PipelineState;
  setProfile: (profile: LandProfile) => void;
  setCapability: (result: CapabilityResult) => void;
  setWatershed: (result: WatershedResult) => void;
  setSwat: (result: SWATResult) => void;
  setRothC: (result: RothCResult) => void;
  setSatellite: (data: SatelliteData) => void;
  setApiResult: (type: string, data: any) => void;
  apiResults: Record<string, any>;
  clearAll: () => void;
  getHistory: () => Array<{ timestamp: string; type: string; data: any }>;
}

const initialState: PipelineState = {
  currentProfile: null,
  capability: null,
  watershed: null,
  swat: null,
  rothc: null,
  satellite: null,
  apiResults: {},
  history: [],
};

const PipelineContext = createContext<PipelineContextType | undefined>(undefined);

export function SimulationPipelineProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PipelineState>(initialState);

  const addToHistory = (type: string, data: any) => {
    setState(prev => ({
      ...prev,
      history: [
        ...prev.history,
        { timestamp: new Date().toISOString(), type, data }
      ].slice(-100), // Keep last 100 entries
    }));
  };

  const setProfile = (profile: LandProfile) => {
    setState(prev => ({ ...prev, currentProfile: profile }));
    addToHistory('profile', profile);
  };

  const setCapability = (result: CapabilityResult) => {
    setState(prev => ({ ...prev, capability: result }));
    addToHistory('capability', result);
  };

  const setWatershed = (result: WatershedResult) => {
    setState(prev => ({ ...prev, watershed: result }));
    addToHistory('watershed', result);
  };

  const setSwat = (result: SWATResult) => {
    setState(prev => ({ ...prev, swat: result }));
    addToHistory('swat', result);
  };

  const setRothC = (result: RothCResult) => {
    setState(prev => ({ ...prev, rothc: result }));
    addToHistory('rothc', result);
  };

  const setSatellite = (data: SatelliteData) => {
    setState(prev => ({ ...prev, satellite: data }));
    addToHistory('satellite', data);
  };

  const setApiResult = (type: string, data: any) => {
    setState(prev => ({
      ...prev,
      apiResults: { ...prev.apiResults, [type]: data },
    }));
    addToHistory(type, data);
  };

  const clearAll = () => {
    setState(initialState);
  };

  const getHistory = () => state.history;

  return (
    <PipelineContext.Provider value={{
      state,
      setProfile,
      setCapability,
      setWatershed,
      setSwat,
      setRothC,
      setSatellite,
      setApiResult,
      apiResults: state.apiResults,
      clearAll,
      getHistory,
    }}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline() {
  const context = useContext(PipelineContext);
  if (!context) {
    // Graceful fallback - return a no-op context
    // This allows components to work even if provider is missing
    console.warn('[Pipeline] Provider not found, using fallback no-op context');
    return {
      state: {
        currentProfile: null,
        capability: null,
        watershed: null,
        swat: null,
        rothc: null,
        satellite: null,
        history: [],
      },
      setProfile: () => {},
      setCapability: () => {},
      setWatershed: () => {},
      setSwat: () => {},
      setRothC: () => {},
      setSatellite: () => {},
      setApiResult: () => {},
      apiResults: {},
      clearAll: () => {},
      getHistory: () => [],
    };
  }
  return context;
}

// Safe version that returns null if provider is missing
export function usePipelineSafe() {
  return useContext(PipelineContext);
}
