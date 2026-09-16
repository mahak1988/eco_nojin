/** Inventory API client — SKU, warehouse, movements, reservations, stocktakes.
 * Follows existing marketplaceApi.ts patterns.
 */

import { getApiBase } from './api';
import type {
  SKU,
  Warehouse,
  Movement,
  Balance,
} from './inventoryTypes';

const apiBase = getApiBase();

async function inventoryFetch<T>(
  path: string,
  options?: RequestInit & { skipAuth?: boolean },
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
    throw new Error((detail as { detail?: string }).detail || `inventory_error_${res.status}`);
  }
  return res.json() as T;
}

// --- SKU ---

export async function fetchSKUs(isActive = true, limit = 100): Promise<SKU[]> {
  const params = new URLSearchParams();
  params.set('is_active', String(isActive));
  params.set('limit', String(limit));
  return inventoryFetch<SKU[]>(`/api/v1/inventory/skus?${params.toString()}`);
}

export async function fetchSKU(skuCode: string): Promise<SKU> {
  return inventoryFetch<SKU>(`/api/v1/inventory/skus/${skuCode}`);
}

export async function createSKU(body: {
  sku_code: string;
  name: string;
  uom?: string;
  category_id?: number;
  standard_cost?: string;
  warehouse_id?: number;
}): Promise<SKU> {
  return inventoryFetch<SKU>('/api/v1/inventory/skus', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// --- Warehouse ---

export async function fetchWarehouses(): Promise<Warehouse[]> {
  return inventoryFetch<Warehouse[]>('/api/v1/inventory/warehouses');
}

export async function createWarehouse(body: {
  code: string;
  name: string;
  city?: string;
}): Promise<Warehouse> {
  return inventoryFetch<Warehouse>('/api/v1/inventory/warehouses', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// --- Stock Movements ---

export async function stockReceipt(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  location_id?: number;
  lot_id?: number;
  unit_cost?: string;
  reference_id?: string;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/receipt', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function stockIssue(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  location_id?: number;
  reference_id?: string;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/issue', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function stockTransfer(body: {
  sku_code: string;
  from_warehouse_id: number;
  to_warehouse_id: number;
  qty: string;
  from_location_id?: number;
  to_location_id?: number;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/transfer', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function stockAdjust(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  reason?: string;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/adjust', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function stockReturn(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  location_id?: number;
  reference_id?: string;
  unit_cost?: string;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/return', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function stockScrap(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  reason?: string;
}): Promise<{ movement_id: number; type: string; qty: string }> {
  return inventoryFetch('/api/v1/inventory/movements/scrap', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchMovements(params?: {
  sku_code?: string;
  warehouse_id?: number;
  movement_type?: string;
  limit?: number;
}): Promise<Movement[]> {
  const qs = new URLSearchParams();
  if (params?.sku_code) qs.set('sku_code', params.sku_code);
  if (params?.warehouse_id !== undefined) qs.set('warehouse_id', String(params.warehouse_id));
  if (params?.movement_type) qs.set('movement_type', params.movement_type);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  return inventoryFetch<Movement[]>(
    `/api/v1/inventory/movements${q ? `?${q}` : ''}`,
  );
}

// --- Balance ---

export async function fetchBalance(
  skuCode: string,
  warehouseId?: number,
): Promise<Balance> {
  const params = new URLSearchParams();
  if (warehouseId !== undefined) params.set('warehouse_id', String(warehouseId));
  const q = params.toString();
  return inventoryFetch<Balance>(
    `/api/v1/inventory/balances/${skuCode}${q ? `?${q}` : ''}`,
  );
}

// --- Reservations ---

export async function reserveStock(body: {
  sku_code: string;
  warehouse_id: number;
  qty: string;
  reference_type?: string;
  reference_id: string;
  reference_line_id?: string;
  expires_at?: string;
}): Promise<{ reservation_id: number; qty: string; status: string }> {
  return inventoryFetch('/api/v1/inventory/reservations', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function consumeReservation(
  reservationId: number,
  qty?: number,
): Promise<{ movement_id: number; qty: string }> {
  const params = qty !== undefined ? `?qty=${qty}` : '';
  return inventoryFetch(`/api/v1/inventory/reservations/${reservationId}/consume${params}`, {
    method: 'POST',
  });
}

export async function releaseReservation(reservationId: number): Promise<{ reservation_id: number; status: string }> {
  return inventoryFetch(`/api/v1/inventory/reservations/${reservationId}/release`, {
    method: 'POST',
  });
}

// --- Stocktakes ---

export async function createStocktake(body: {
  warehouse_id: number;
  lines: Array<{ sku_id: number; location_id?: number; lot_id?: number; counted_qty: string }>;
}): Promise<{ stocktake_id: number; stocktake_number: string; status: string }> {
  return inventoryFetch('/api/v1/inventory/stocktakes', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function approveStocktake(stocktakeId: number): Promise<{ stocktake_id: number; status: string; approved_by: string | null }> {
  return inventoryFetch(`/api/v1/inventory/stocktakes/${stocktakeId}/approve`, {
    method: 'POST',
  });
}

// --- Reconciliation ---

export async function reconcileInventory(): Promise<Record<string, unknown>> {
  return inventoryFetch<Record<string, unknown>>('/api/v1/inventory/reconcile', {
    method: 'POST',
  });
}

