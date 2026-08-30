/**
 * Marketplace API Functions
 * ===========================
 * @module features/marketplace/api
 */

import type { Product, Order, MarketplaceStats } from '../types';
import { ENDPOINTS } from '../constants/config';
import { normalizeOrderStatus } from '../constants/orderStatus';

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/** Normalize API array/object response */
function normalizeArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    const obj = data as { items?: T[]; products?: T[]; orders?: T[] };
    return obj.items || obj.products || obj.orders || [];
  }
  return [];
}

/** Fetch all products */
export async function fetchProducts(): Promise<Product[]> {
  const response = await fetch(ENDPOINTS.products, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.statusText}`);
  }
  const data = await response.json();
  return normalizeArray<Product>(data);
}

/** Fetch all orders with status normalization */
export async function fetchOrders(): Promise<Order[]> {
  const response = await fetch(ENDPOINTS.orders, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch orders: ${response.statusText}`);
  }
  const data = await response.json();
  const raw = normalizeArray<Order>(data);
  // Normalize status field
  return raw.map((o) => ({
    ...o,
    status: normalizeOrderStatus(o.status),
  }));
}

/** Fetch marketplace statistics */
export async function fetchMarketplaceStats(): Promise<MarketplaceStats> {
  const response = await fetch(ENDPOINTS.stats, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }
  return response.json() as Promise<MarketplaceStats>;
}

/** Confirm a pending order (mutation) */
export async function confirmOrderApi(orderId: string): Promise<void> {
  const response = await fetch(ENDPOINTS.confirmOrder(orderId), {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to confirm order: ${response.statusText}`);
  }
}
