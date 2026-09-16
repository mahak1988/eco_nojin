/** Issuance API client — carbon credit issuance, registry, and gate tracking.
 * Uses real backend endpoints (blockchain/carbon, audit) where they exist;
 * missing endpoints fall back to simulation/pre-verification mode with
 * transparent simulation indicators in responses. */

import { getApiBase } from './api';
import type {
  IssuanceRecord,
  IssuanceListResponse,
  IssuanceCreateRequest,
  IssuanceCreateResponse,
} from '../types/issuance';

const apiBase = getApiBase();

async function issuanceFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydroma_token');
  if (token && !options?.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `issuance_error_${res.status}`);
  }
  return res.json() as T;
}

function simulationOnly<T>(data: T): T & { _simulation: boolean } {
  return { ...data, _simulation: true } as T & { _simulation: boolean };
}

/** Lists issuance records — uses /api/v1/audit/credits (real) or simulation fallback. */
export async function fetchIssuanceRecords(params?: {
  projectId?: string;
  phase?: string;
  verificationLabel?: string;
  limit?: number;
}): Promise<IssuanceListResponse> {
  const qs = new URLSearchParams();
  if (params?.projectId) qs.set('projectId', params.projectId);
  if (params?.phase) qs.set('phase', params.phase);
  if (params?.verificationLabel) qs.set('verificationLabel', params.verificationLabel);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  try {
    return await issuanceFetch<IssuanceListResponse>(
      `/api/v1/audit/credits${q ? `?${q}` : ''}`,
    );
  } catch {
    return simulationOnly<IssuanceListResponse>({
      records: [],
      total: 0,
      simulationOnly: true,
    });
  }
}

/** Creates an issuance record — uses /api/v1/blockchain/carbon/projects/{id}/issue (real) or simulation fallback. */
export async function createIssuanceRecord(
  body: IssuanceCreateRequest,
): Promise<IssuanceCreateResponse> {
  try {
    return await issuanceFetch<IssuanceCreateResponse>(
      `/api/v1/blockchain/carbon/projects/${body.projectId}/issue`,
      {
        method: 'POST',
        body: JSON.stringify({ amount: body.simulatedAmount, owner: body.projectId }),
      },
    );
  } catch {
    return {
      id: `sim-${Date.now()}`,
      status: 'simulated',
      verificationLabel: 'not_certified',
      gates: [
        { gate: 'VVB', status: 'pending', note: 'pre-verification simulation' },
        { gate: 'registry', status: 'pending', note: 'simulated' },
        { gate: 'legal', status: 'pending', note: 'awaiting compliance review' },
      ],
      idempotencyKey: body.idempotencyKey,
      _simulation: true,
    } as IssuanceCreateResponse;
  }
}

/** Fetches a single issuance record by ID — uses /api/v1/blockchain/carbon/credits/{id} (real) or simulation fallback. */
export async function fetchIssuanceRecord(id: string): Promise<IssuanceRecord> {
  try {
    const rec = await issuanceFetch<IssuanceRecord>(
      `/api/v1/blockchain/carbon/credits/${id}`,
    );
    return { ...rec, _simulation: false } as IssuanceRecord;
  } catch {
    return {
      id,
      projectId: '',
      phase: 'phase2_carbon',
      verificationLabel: 'not_certified',
      gates: [
        { gate: 'VVB', status: 'pending', note: 'pre-verification simulation' },
        { gate: 'registry', status: 'pending', note: 'simulated' },
        { gate: 'legal', status: 'pending', note: 'awaiting compliance review' },
      ],
      simulatedAmount: 0,
      unit: 'tCO2e',
      freezeStatus: 'active',
      retirementStatus: 'pending',
      idempotencyKey: null,
      registryEntry: 'simulated',
      verificationLabel: 'not_certified',
      methodology: 'Simulation pre-verification',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      _simulation: true,
    } as IssuanceRecord;
  }
}

/** Checks registry entry — uses /api/v1/blockchain/carbon/projects/{id} (real) or simulation fallback. */
export async function checkRegistryEntry(id: string): Promise<{
  id: string;
  simulated: boolean;
  verificationLabel: string;
  gates: { gate: string; status: string }[];
}> {
  try {
    const res = await issuanceFetch<{ project_id?: string; verified?: boolean }>(
      `/api/v1/blockchain/carbon/projects/${id}`,
    );
    return {
      id,
      simulated: false,
      verificationLabel: res.verified ? 'field_verified' : 'not_certified',
      gates: [
        { gate: 'VVB', status: res.verified ? 'passed' : 'pending' },
        { gate: 'registry', status: res.verified ? 'passed' : 'pending' },
        { gate: 'legal', status: 'pending' },
      ],
    };
  } catch {
    return {
      id,
      simulated: true,
      verificationLabel: 'not_certified',
      gates: [
        { gate: 'VVB', status: 'pending', note: 'pre-verification simulation' },
        { gate: 'registry', status: 'pending', note: 'simulated' },
        { gate: 'legal', status: 'pending', note: 'awaiting compliance review' },
      ],
    };
  }
}
