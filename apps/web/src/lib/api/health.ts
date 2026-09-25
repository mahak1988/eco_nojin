import { apiGet } from './client';
import type { ServiceOverview, ServiceStatus } from './public';

const healthEndpoints: Array<{ id: string; name: string; path: string }> = [
  { id: 'platform', name: 'Platform', path: '/api/v1/platform/health' },
  { id: 'satellite', name: 'Satellite', path: '/api/v1/satellite/health' },
  { id: 'voice', name: 'Voice', path: '/api/v1/voice/health' },
  { id: 'ai', name: 'AI', path: '/api/v1/ai/health' },
  { id: 'land', name: 'Land', path: '/api/v1/land/health' },
  { id: 'blockchain', name: 'Blockchain', path: '/api/v1/blockchain/health' },
  { id: 'automation', name: 'Automation', path: '/api/v1/automation/health' },
  { id: 'ecowallet', name: 'EcoWallet', path: '/api/v1/ecowallet/health' },
];

async function readHealth(endpoint: {
  id: string;
  name: string;
  path: string;
}): Promise<ServiceStatus> {
  const checkedAt = new Date().toISOString();
  const result = await apiGet<Record<string, unknown>>(endpoint.path);
  return {
    id: endpoint.id,
    name: endpoint.name,
    status: result.ok ? 'operational' : 'degraded',
    lastCheck: checkedAt,
    provenance: {
      source: 'API Gateway health endpoint',
      verified: result.ok,
      method: 'GET /health',
    },
  };
}

export async function getServiceOverview(): Promise<
  { ok: true; data: ServiceOverview; status: number } | { ok: false; error: string; status: number }
> {
  const results = await Promise.all(healthEndpoints.map(readHealth));
  const operational = results.filter((service) => service.status === 'operational').length;
  const degraded = results.filter((service) => service.status === 'degraded').length;
  if (operational === 0) {
    return { ok: false, error: 'All service health endpoints are unavailable', status: 503 };
  }
  return {
    ok: true,
    status: 200,
    data: {
      services: results,
      summary: {
        total: results.length,
        operational,
        degraded,
        offline: 0,
      },
      provenance: {
        source: 'API Gateway health endpoints',
        verified: true,
        method: 'GET /health',
      },
    },
  };
}

export async function getServiceStatus(
  serviceId: string,
): Promise<
  { ok: true; data: ServiceStatus; status: number } | { ok: false; error: string; status: number }
> {
  const endpoint = healthEndpoints.find((service) => service.id === serviceId);
  if (!endpoint) return { ok: false, error: 'Unknown service', status: 404 };
  const status = await readHealth(endpoint);
  return status.status === 'operational'
    ? { ok: true, data: status, status: 200 }
    : { ok: false, error: 'Service health endpoint unavailable', status: 503 };
}
