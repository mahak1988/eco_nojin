/**
 * Simulator API Service - اتصال به Backend شبیه‌سازها
 */

const API_BASE = 'http://localhost:8000/api/v1';

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
  crop?: {
    cropType: string;
    plantingDate: string;
  };
  windbreak?: {
    treeSpecies: string;
    heightM: number;
    lengthM: number;
    porosityPct: number;
  };
  multiLayer?: {
    canopyLayer: { cropType: string; plantingDate: string };
    subCanopyLayer?: { cropType: string; plantingDate: string };
    groundLayer?: { cropType: string; plantingDate: string };
    shadeTolerance: number;
  };
}

export interface SimulationResult {
  simulationId: string;
  simulationType: string;
  status: string;
  summary: Record<string, any>;
  timeSeries?: Array<Record<string, any>>;
  warnings?: string[];
  error?: string;
}

export interface LivestockRequest {
  herd: {
    animalType: 'cattle' | 'sheep' | 'goat' | 'poultry';
    headCount: number;
    breed?: string;
    productionSystem: 'grazing' | 'mixed' | 'intensive';
  };
  forage: {
    ndviValue: number;
    crudeProteinPct: number;
    digestibilityPct: number;
    dryMatterTonHa: number;
  };
  landAreaHa: number;
  waterAvailabilityM3Day: number;
}

export interface LivestockResult {
  simulationId: string;
  animalType: string;
  herdSize: number;
  status: string;
  production: {
    milkKgDay: number;
    meatKgYear: number;
    woolKgYear: number;
    eggsDay: number;
    offspringPerYear: number;
  };
  economics: {
    grossRevenueUsdYear: number;
    netProfitUsdYear: number;
    profitMarginPct: number;
  };
  environmental: {
    methaneKgCo2eYear: number;
    waterFootprintM3Year: number;
    grazingPressureIndex: number;
  };
  manure: {
    totalKgYear: number;
    nitrogenKgYear: number;
    organicCarbonKgYear: number;
  };
}

class SimulatorService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }

  // ─── Crop Simulation ─────────────────────────────
  async simulateCropGrowth(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', {
      method: 'POST',
      body: JSON.stringify({
        simulation_type: 'crop_growth',
        context,
      }),
    });
  }

  // ─── Carbon Simulation ─────────────────────────────
  async simulateCarbonSequestration(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', {
      method: 'POST',
      body: JSON.stringify({
        simulation_type: 'soil_carbon',
        context,
      }),
    });
  }

  // ─── Erosion Simulation ─────────────────────────────
  async simulateErosion(context: SimulationContext): Promise<{
    wind: SimulationResult;
    water: SimulationResult;
  }> {
    return this.request('/simulation/erosion-analysis', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Windbreak Design ─────────────────────────────
  async designWindbreak(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/windbreak-design', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Multi-Layer Cropping ─────────────────────────────
  async planMultiLayerCropping(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/multi-layer-plan', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Water Budget ─────────────────────────────
  async analyzeWaterBudget(context: SimulationContext): Promise<{
    infiltration: SimulationResult;
    watershed: SimulationResult;
  }> {
    return this.request('/simulation/water-budget', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Comprehensive Analysis ─────────────────────────────
  async runComprehensiveAnalysis(context: SimulationContext): Promise<Record<string, SimulationResult>> {
    return this.request('/simulation/comprehensive', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Livestock Simulation ─────────────────────────────
  async simulateLivestock(request: LivestockRequest): Promise<LivestockResult> {
    return this.request('/livestock/simulate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ─── Compare Livestock Scenarios ─────────────────────────────
  async compareLivestockScenarios(requests: LivestockRequest[]): Promise<LivestockResult[]> {
    return this.request('/livestock/compare', {
      method: 'POST',
      body: JSON.stringify(requests),
    });
  }

  // ─── Get Available Simulators ─────────────────────────────
  async listSimulators(): Promise<Array<{ type: string; name: string; version: string }>> {
    return this.request('/simulation/simulators');
  }
}

export const simulatorService = new SimulatorService();
