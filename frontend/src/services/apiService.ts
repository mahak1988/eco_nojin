/**
 * Graceful API Service
 * Handles 404s and errors gracefully without breaking UI
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface ApiResult<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  status?: number;
}

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Graceful GET - returns null on 404 instead of throwing
   */
  async get<T>(endpoint: string, fallback: T | null = null): Promise<ApiResult<T>> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (response.status === 404) {
        console.warn(`[API] 404 Not Found: ${endpoint} - Using fallback`);
        return { success: false, data: fallback, error: 'Not found', status: 404 };
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] Error ${response.status}: ${endpoint}`, errorText);
        return { success: false, data: fallback, error: errorText, status: response.status };
      }

      const data = await response.json();
      return { success: true, data, error: null, status: response.status };
    } catch (error: any) {
      console.error(`[API] Network error: ${endpoint}`, error);
      return { success: false, data: fallback, error: error.message };
    }
  }

  /**
   * Graceful POST - returns null on error instead of throwing
   */
  async post<T, B = any>(
    endpoint: string,
    body: B,
    fallback: T | null = null
  ): Promise<ApiResult<T>> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(body),
      });

      if (response.status === 404) {
        console.warn(`[API] 404 Not Found: ${endpoint} - Using fallback`);
        return { success: false, data: fallback, error: 'Not found', status: 404 };
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] Error ${response.status}: ${endpoint}`, errorText);
        return { success: false, data: fallback, error: errorText, status: response.status };
      }

      const data = await response.json();
      return { success: true, data, error: null, status: response.status };
    } catch (error: any) {
      console.error(`[API] Network error: ${endpoint}`, error);
      return { success: false, data: fallback, error: error.message };
    }
  }

  // ===== Specific API Methods =====

  /**
   * Get security status - uses correct endpoint or falls back
   */
  async getSecurityStatus(): Promise<ApiResult<any>> {
    // Try correct endpoint first
    const result = await this.get('/security/status', {
      status: 'operational',
      last_check: new Date().toISOString(),
      alerts: [],
    });
    return result;
  }

  /**
   * Get climate data - uses correct endpoint
   */
  async getClimateData(params: { lat: number; lon: number }): Promise<ApiResult<any>> {
    return await this.post('/climate', params, {
      temperature: 25,
      precipitation: 0,
      humidity: 50,
      status: 'normal',
    });
  }

  /**
   * Get drought data - uses correct endpoint
   */
  async getDroughtData(params: { lat: number; lon: number }): Promise<ApiResult<any>> {
    // drought uses /climate endpoint
    return await this.post(
      '/climate',
      { ...params, check_drought: true },
      {
        drought_index: 0.3,
        status: 'normal',
        severity: 'none',
      }
    );
  }

  /**
   * Get LMS courses - not implemented, graceful fallback
   */
  async getLMSCourses(): Promise<ApiResult<any>> {
    return await this.get('/lms/courses', {
      courses: [],
      status: 'coming_soon',
      message: 'LMS module is under development',
    });
  }

  /**
   * Get insurance capabilities
   */
  async getInsuranceCapabilities(): Promise<ApiResult<any>> {
    return await this.get('/insurance/capabilities', {
      capabilities: [],
      status: 'coming_soon',
    });
  }

  /**
   * Get tourism status
   */
  async getTourismStatus(): Promise<ApiResult<any>> {
    return await this.get('/tourism/status', {
      status: 'coming_soon',
      tours: [],
      message: 'Tourism module is under development',
    });
  }
}

export const apiService = new ApiService();
export default apiService;
