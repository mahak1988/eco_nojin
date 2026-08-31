/**
 * Motors Service - Connects to scientific motors backend
 * Endpoints: /api/v1/motors/*
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface Motor {
  key: string;
  name: string;
  description?: string;
  category?: string;
  status?: 'available' | 'running' | 'error';
  parameters?: MotorParameter[];
}

export interface MotorParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select';
  default?: any;
  min?: number;
  max?: number;
  options?: string[];
  description?: string;
}

export interface MotorRunRequest {
  motor_key: string;
  parameters: Record<string, any>;
}

export interface MotorRunResponse {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export interface ChainRunRequest {
  motors: MotorRunRequest[];
}

class MotorsService {
  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    return response.json();
  }

  /**
   * Get list of available motors
   * GET /api/v1/motors/list
   */
  async listMotors(): Promise<Motor[]> {
    try {
      const data = await this.request<any>('/motors/list');
      return data.motors || data || [];
    } catch (error) {
      console.error('Failed to fetch motors:', error);
      // Fallback to static list
      return this.getFallbackMotors();
    }
  }

  /**
   * Run a single motor
   * POST /api/v1/motors/run
   */
  async runMotor(request: MotorRunRequest): Promise<MotorRunResponse> {
    return this.request<MotorRunResponse>('/motors/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Run a chain of motors
   * POST /api/v1/motors/chain
   */
  async runChain(request: ChainRunRequest): Promise<MotorRunResponse> {
    return this.request<MotorRunResponse>('/motors/chain', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get run status
   * GET /api/v1/motors/status/{run_id}
   */
  async getRunStatus(runId: string): Promise<MotorRunResponse> {
    return this.request<MotorRunResponse>(`/motors/status/${runId}`);
  }

  /**
   * Check motors health
   * GET /api/v1/motors/health
   */
  async getHealth(): Promise<any> {
    return this.request<any>('/motors/health');
  }

  /**
   * Fallback list of motors (based on backend analysis)
   */
  getFallbackMotors(): Motor[] {
    return [
      {
        key: 'aquacrop',
        name: 'AquaCrop',
        description: 'Crop growth simulation based on water productivity (FAO)',
        category: 'Crop',
        parameters: [
          {
            name: 'crop_type',
            type: 'select',
            options: ['wheat', 'corn', 'barley', 'alfalfa'],
            description: 'Type of crop',
          },
          {
            name: 'planting_date',
            type: 'string',
            default: '2024-10-01',
            description: 'Planting date',
          },
          { name: 'irrigation', type: 'boolean', default: true, description: 'Enable irrigation' },
          {
            name: 'soil_type',
            type: 'select',
            options: ['clay', 'loam', 'sand'],
            description: 'Soil type',
          },
        ],
      },
      {
        key: 'rothc',
        name: 'RothC',
        description: 'Soil carbon dynamics model',
        category: 'Soil',
        parameters: [
          {
            name: 'initial_carbon',
            type: 'number',
            default: 20,
            min: 1,
            max: 100,
            description: 'Initial soil carbon (t/ha)',
          },
          {
            name: 'years',
            type: 'number',
            default: 10,
            min: 1,
            max: 100,
            description: 'Simulation years',
          },
          {
            name: 'clay_content',
            type: 'number',
            default: 25,
            min: 5,
            max: 70,
            description: 'Clay content (%)',
          },
        ],
      },
      {
        key: 'swat',
        name: 'SWAT+',
        description: 'Soil and Water Assessment Tool - Hydrology simulation',
        category: 'Hydrology',
        parameters: [
          {
            name: 'watershed_area',
            type: 'number',
            default: 100,
            min: 1,
            max: 10000,
            description: 'Watershed area (km²)',
          },
          {
            name: 'rainfall',
            type: 'number',
            default: 300,
            min: 50,
            max: 2000,
            description: 'Annual rainfall (mm)',
          },
          {
            name: 'land_use',
            type: 'select',
            options: ['cropland', 'forest', 'grassland', 'urban'],
            description: 'Land use',
          },
        ],
      },
      {
        key: 'hecras',
        name: 'HEC-RAS',
        description: 'Flood wave routing and hydraulic analysis',
        category: 'Hydraulics',
        parameters: [
          {
            name: 'river_length',
            type: 'number',
            default: 10,
            min: 1,
            max: 1000,
            description: 'River length (km)',
          },
          {
            name: 'slope',
            type: 'number',
            default: 0.001,
            min: 0.0001,
            max: 0.1,
            description: 'River slope',
          },
          {
            name: 'flow',
            type: 'number',
            default: 50,
            min: 1,
            max: 10000,
            description: 'Flow rate (m³/s)',
          },
        ],
      },
      {
        key: 'rusle',
        name: 'RUSLE',
        description: 'Soil erosion model (Universal Soil Loss Equation)',
        category: 'Soil',
        parameters: [
          {
            name: 'slope_percent',
            type: 'number',
            default: 5,
            min: 0,
            max: 100,
            description: 'Slope (%)',
          },
          {
            name: 'slope_length',
            type: 'number',
            default: 100,
            min: 10,
            max: 1000,
            description: 'Slope length (m)',
          },
          {
            name: 'rainfall_intensity',
            type: 'number',
            default: 100,
            min: 10,
            max: 500,
            description: 'Rainfall intensity',
          },
        ],
      },
      {
        key: 'carbon_sequestration',
        name: 'Carbon Sequestration',
        description: 'Carbon sequestration estimation',
        category: 'Carbon',
        parameters: [
          {
            name: 'area',
            type: 'number',
            default: 10,
            min: 1,
            max: 1000,
            description: 'Area (ha)',
          },
          {
            name: 'species',
            type: 'select',
            options: ['pistachio', 'almond', 'olive', 'pomegranate'],
            description: 'Tree species',
          },
          {
            name: 'years',
            type: 'number',
            default: 20,
            min: 5,
            max: 100,
            description: 'Project years',
          },
        ],
      },
      {
        key: 'irrigation_scheduler',
        name: 'Irrigation Scheduler',
        description: 'Optimal irrigation scheduling',
        category: 'Irrigation',
        parameters: [
          {
            name: 'crop',
            type: 'select',
            options: ['wheat', 'corn', 'tomato', 'cucumber'],
            description: 'Crop type',
          },
          {
            name: 'soil_type',
            type: 'select',
            options: ['clay', 'loam', 'sand'],
            description: 'Soil type',
          },
          {
            name: 'area',
            type: 'number',
            default: 1,
            min: 0.1,
            max: 100,
            description: 'Area (ha)',
          },
        ],
      },
      {
        key: 'planting_calendar',
        name: 'Planting Calendar',
        description: 'Optimal planting dates based on climate',
        category: 'Crop',
        parameters: [
          {
            name: 'region',
            type: 'select',
            options: ['arid', 'semi-arid', 'temperate', 'humid'],
            description: 'Climate region',
          },
          {
            name: 'crop',
            type: 'select',
            options: ['wheat', 'corn', 'barley', 'potato'],
            description: 'Crop type',
          },
        ],
      },
      {
        key: 'land_capability',
        name: 'Land Capability',
        description: 'Land capability classification (FAO)',
        category: 'Land',
        parameters: [
          { name: 'slope', type: 'number', default: 3, min: 0, max: 50, description: 'Slope (%)' },
          {
            name: 'soil_depth',
            type: 'number',
            default: 100,
            min: 10,
            max: 500,
            description: 'Soil depth (cm)',
          },
          {
            name: 'drainage',
            type: 'select',
            options: ['excessive', 'well', 'moderate', 'poor', 'very_poor'],
            description: 'Drainage class',
          },
        ],
      },
      {
        key: 'crop_advisor',
        name: 'Crop Advisor',
        description: 'AI-based crop recommendation',
        category: 'Crop',
        parameters: [
          { name: 'soil_ph', type: 'number', default: 7.0, min: 4, max: 9, description: 'Soil pH' },
          {
            name: 'water_availability',
            type: 'select',
            options: ['high', 'medium', 'low'],
            description: 'Water availability',
          },
          {
            name: 'market_access',
            type: 'select',
            options: ['high', 'medium', 'low'],
            description: 'Market access',
          },
        ],
      },
    ];
  }

  /**
   * Get motors by category
   */
  getMotorsByCategory(motors: Motor[]): Record<string, Motor[]> {
    return motors.reduce(
      (acc, motor) => {
        const category = motor.category || 'Other';
        if (!acc[category]) acc[category] = [];
        acc[category].push(motor);
        return acc;
      },
      {} as Record<string, Motor[]>
    );
  }
}

export const motorsService = new MotorsService();
export default motorsService;
