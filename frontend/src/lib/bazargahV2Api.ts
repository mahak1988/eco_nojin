/** Bazargah plan-v2.0 API client — disputes, logistics, quality (follows marketplaceApi.ts patterns). */

import { getApiBase } from './api';

const apiBase = getApiBase();

async function v2Fetch<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydroma_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    throw new Error(`bazargah_v2_error_${res.status}`);
  }
  return res.json() as T;
}

// --- Disputes ---

export interface DisputeDto {
  id: string;
  order_id: string;
  status: string; // open | under_review | resolved | rejected | escalated
  category: string; // quality | delivery | payment | other
  description: string;
  resolution: string | null;
  resolved_by: string | null;
  created_at: string | null;
}

export async function createDispute(payload: {
  order_id: string;
  category: string;
  description: string;
}): Promise<{ ok: boolean; dispute: DisputeDto }> {
  return v2Fetch('/api/v1/disputes', { method: 'POST', body: JSON.stringify(payload) });
}

export async function listDisputes(status?: string): Promise<{ count: number; disputes: DisputeDto[] }> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return v2Fetch(`/api/v1/disputes${qs}`);
}

export async function escalateDispute(disputeId: string, actor: string): Promise<{ ok: boolean; dispute: DisputeDto }> {
  return v2Fetch(`/api/v1/disputes/${disputeId}/escalate?actor=${encodeURIComponent(actor)}`, { method: 'POST' });
}

// --- Logistics ---

export interface ShipmentDto {
  id: string;
  order_id: string;
  status: string; // pending | picked_up | in_transit | delivered | failed
  carrier: string | null;
  tracking_code: string | null;
}

export async function createShipment(payload: {
  order_id: string;
  carrier?: string;
  origin?: string;
  destination?: string;
}): Promise<{ ok: boolean; id: string; status: string }> {
  return v2Fetch('/api/v1/logistics/shipments', { method: 'POST', body: JSON.stringify(payload) });
}

export async function getShipment(shipmentId: string): Promise<{ shipment: ShipmentDto }> {
  return v2Fetch(`/api/v1/logistics/shipments/${shipmentId}`);
}

export async function updateShipmentStatus(
  shipmentId: string,
  payload: { status: string; actor?: string; note?: string },
): Promise<{ ok: boolean; id: string; status: string }> {
  return v2Fetch(`/api/v1/logistics/shipments/${shipmentId}/status`, { method: 'POST', body: JSON.stringify(payload) });
}

// --- Quality ---

export interface InspectionDto {
  id: string;
  product_id: string;
  status: string; // pending | passed | failed
  score: number | null;
}

export async function createInspection(payload: {
  product_id: string;
  inspection_type: string; // harvest | packaging | delivery
  marketplace_id?: string;
}): Promise<{ ok: boolean; id: string; status: string }> {
  return v2Fetch('/api/v1/quality/inspections', { method: 'POST', body: JSON.stringify(payload) });
}

export async function recordInspectionResult(
  inspectionId: string,
  payload: { score: number; notes?: string },
): Promise<{ ok: boolean; status: string; score: number; certificate_id: string | null }> {
  return v2Fetch(`/api/v1/quality/inspections/${inspectionId}/result`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function listInspections(productId?: string): Promise<{ count: number; inspections: InspectionDto[] }> {
  const qs = productId ? `?product_id=${encodeURIComponent(productId)}` : '';
  return v2Fetch(`/api/v1/quality/inspections${qs}`);
}
