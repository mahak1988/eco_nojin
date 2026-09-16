/** Commerce API client — orders, payments, settlements.
 * Follows existing marketplaceApi.ts patterns with Idempotency-Key header.
 */

import { getApiBase } from './api';
import type { Order, OrderResponse, Settlement } from './commerceTypes';

const apiBase = getApiBase();

function idemKey(): string {
  return (crypto?.randomUUID?.() ?? `idem-${Date.now()}-${Math.random().toString(36).slice(2)}`);
}

async function commerceFetch<T>(
  path: string,
  options?: RequestInit & { skipAuth?: boolean },
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Idempotency-Key': idemKey(),
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydroma_token');
  if (token && !options?.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `commerce_error_${res.status}`);
  }
  return res.json() as T;
}

// --- Orders ---

export async function fetchOrders(params?: {
  status?: string;
  buyer_id?: string;
  limit?: number;
}): Promise<{ orders: Order[]; count: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.buyer_id) qs.set('buyer_id', params.buyer_id);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  return commerceFetch<{ orders: Order[]; count: number }>(
    `/api/v1/commerce/orders${q ? `?${q}` : ''}`,
  );
}

export async function fetchOrder(orderId: string): Promise<Order> {
  return commerceFetch<Order>(`/api/v1/commerce/orders/${orderId}`);
}

export async function createOrder(body: {
  items: Array<{ sku_code: string; quantity: string; unit_price?: string; warehouse_id?: number | null }>;
  shipping_address?: Record<string, unknown> | null;
  idempotency_key?: string | null;
}): Promise<OrderResponse> {
  return commerceFetch<OrderResponse>('/api/v1/commerce/orders', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// --- Order Lifecycle ---

export async function payOrder(
  orderId: string,
  provider = 'wallet',
): Promise<{ payment_id: string; order_id: string; amount: string; currency: string; status: string; provider: string }> {
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/pay`, {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId, provider, idempotency_key: idemKey() }),
  });
}

export async function confirmPayment(orderId: string): Promise<{ order_id: string; status: string; payment_status: string }> {
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/confirm-payment`, {
    method: 'POST',
  });
}

export async function shipOrder(
  orderId: string,
  trackingCode: string,
): Promise<{ order_id: string; status: string; tracking_code: string }> {
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/ship`, {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId, tracking_code: trackingCode }),
  });
}

export async function markDelivered(orderId: string): Promise<{ order_id: string; status: string }> {
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/mark-delivered`, {
    method: 'POST',
  });
}

export async function cancelOrder(
  orderId: string,
  reason?: string,
): Promise<{ order_id: string; status: string; cancel_reason: string | null }> {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/cancel${params}`, {
    method: 'POST',
  });
}

export async function settleOrder(orderId: string): Promise<{ settlement_id: string; amount: string; status: string; journal_batch_id: string | null }> {
  return commerceFetch(`/api/v1/commerce/orders/${orderId}/settle`, {
    method: 'POST',
  });
}

export async function getAllowedTransitions(orderId: string): Promise<string[]> {
  return commerceFetch<string[]>(`/api/v1/commerce/orders/${orderId}/transitions`);
}

// --- Settlements ---

export async function fetchSettlements(): Promise<Settlement[]> {
  return commerceFetch<Settlement[]>('/api/v1/commerce/settlements');
}
