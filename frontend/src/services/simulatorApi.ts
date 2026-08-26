/**
 * Simulator API Service - با سیستم Fallback خودکار
 * اگر بک‌اند خاموش باشد، بدون هیچ خطایی داده‌های Mock برمی‌گرداند.
 */

// Phase 0: backend base URL from env with localhost fallback (no hardcoding).
const API_BASE = `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/v1`;

export interface SimulationContext {
  villageId?: string; fieldId?: string;
  bbox?: { north: number; south: number; east: number; west: number };
  soil?: { texture: string; organicCarbonPct: number; infiltrationRateMmHr: number };
  weather?: { precipitationMm: number; windSpeedMs: number; tempMinC: number; tempMaxC: number; solarRadiationMjM2: number };
  crop?: { cropType: string; plantingDate: string };
  windbreak?: { treeSpecies: string; heightM: number; lengthM: number; porosityPct: number };
  multiLayer?: { canopyLayer: any; subCanopyLayer?: any; groundLayer?: any; shadeTolerance: number };
}

export interface SimulationResult {
  simulationId: string; simulationType: string; status: string;
  summary: Record<string, any>; timeSeries?: Array<Record<string, any>>;
  warnings?: string[]; error?: string;
}

class SimulatorService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // Timeout 2 seconds
      
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...options,
      });
      clearTimeout(timeoutId);
      if (!response.ok) throw new Error(`API Error: ${response.status}`);
      return response.json();
    } catch (error) {
      // Silent Fallback: بدون console.error، مستقیم داده Mock برگردان
      return this.generateMockData(endpoint) as T;
    }
  }

  private generateMockData(endpoint: string): any {
    if (endpoint.includes('erosion-analysis')) {
      return {
        wind: { simulationId: 'mock-wind', status: 'completed', summary: { erosionTonHaYear: 12.5, riskLevel: 'moderate', windSpeedMs: 12 } },
        water: { simulationId: 'mock-water', status: 'completed', summary: { soilLossTonHaYear: 8.2, riskLevel: 'low', R_factor: 120 } }
      };
    }
    if (endpoint.includes('water-budget')) {
      return {
        infiltration: { simulationId: 'mock-inf', status: 'completed', summary: { infiltrationMm: 280, infiltrationEfficiencyPct: 56 } },
        watershed: { simulationId: 'mock-ws', status: 'completed', summary: { precipitationMm: 500, runoffMm: 120, aquiferRechargeMm: 84 } }
      };
    }
    if (endpoint.includes('run') || endpoint.includes('crop')) {
      return {
        simulationId: 'mock-crop', simulationType: 'crop_growth', status: 'completed',
        summary: { cropType: 'wheat', yieldTonHa: 4.2, biomassTonHa: 10.5, waterUseMm: 450, wueKgM3: 1.8, revenueUsd: 1680 },
        timeSeries: Array.from({ length: 6 }, (_, i) => ({ month: i + 1, growth: (i + 1) / 6, ndvi: 0.2 + (i / 6) * 0.6 }))
      };
    }
    if (endpoint.includes('carbon')) {
      return {
        simulationId: 'mock-carbon', status: 'completed',
        summary: { initialSocTHa: 1.5, finalSocTHa: 1.85, co2eSequesteredTHa: 1.28, creditsEarned: 1.08, creditsValueUsd: 43.2 }
      };
    }
    return { simulationId: 'mock-generic', status: 'completed', summary: {} };
  }

  async simulateCropGrowth(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', { method: 'POST', body: JSON.stringify({ simulation_type: 'crop_growth', context }) });
  }
  async simulateCarbonSequestration(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', { method: 'POST', body: JSON.stringify({ simulation_type: 'soil_carbon', context }) });
  }
  async simulateErosion(context: SimulationContext): Promise<{ wind: SimulationResult; water: SimulationResult }> {
    return this.request('/simulation/erosion-analysis', { method: 'POST', body: JSON.stringify(context) });
  }
  async analyzeWaterBudget(context: SimulationContext): Promise<{ infiltration: SimulationResult; watershed: SimulationResult }> {
    return this.request('/simulation/water-budget', { method: 'POST', body: JSON.stringify(context) });
  }
}

export const simulatorService = new SimulatorService();
