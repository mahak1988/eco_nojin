/**
 * Simulation Service - Connects to simulation endpoints
 * Endpoints: /api/v1/simulation/*
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface SimulationRunRequest {
  model: string;
  parameters: Record<string, any>;
  scenario?: string;
}

export interface SimulationRun {
  id: string;
  model: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  result?: any;
  error?: string;
}

class SimulationService {
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
   * Run a simulation
   * POST /api/v1/simulation/run
   */
  async run(request: SimulationRunRequest): Promise<SimulationRun> {
    return this.request<SimulationRun>('/simulation/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get simulation runs
   * GET /api/v1/simulation/runs
   */
  async listRuns(): Promise<SimulationRun[]> {
    try {
      const data = await this.request<any>('/simulation/runs');
      return data.runs || data || [];
    } catch (error) {
      console.error('Failed to fetch runs:', error);
      return [];
    }
  }

  /**
   * Get model info
   * GET /api/v1/models/{slug}
   */
  async getModelInfo(slug: string): Promise<any> {
    return this.request<any>(`/models/${slug}`);
  }

  /**
   * Run a model directly
   * POST /api/v1/models/{slug}/run
   */
  async runModel(slug: string, parameters: Record<string, any>): Promise<any> {
    return this.request<any>(`/models/${slug}/run`, {
      method: 'POST',
      body: JSON.stringify(parameters),
    });
  }
}

export const simulationService = new SimulationService();
export default simulationService;
