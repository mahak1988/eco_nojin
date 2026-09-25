import {
  type ApiResult,
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
  createIdempotencyKey,
} from './client';

export type { ApiErr, ApiOk, ApiResult } from './client';

const MARKETPLACE_BASE = '/api/v1/marketplace';

/**
 * Shapes below mirror the gateway payloads one-to-one. Nothing is defaulted or
 * invented client-side, so a missing field stays missing and the UI can show an
 * unavailable state instead of a fabricated zero.
 */
export interface CartLine {
  product_id: string;
  product_name?: string;
  quantity: number;
  price?: number;
}

export interface CartResponse {
  cart_id: string | null;
  items: CartLine[];
  total_items: number;
  subtotal: number;
}

export interface AddToCartItem {
  productId: string;
  quantity: number;
}

export interface CreateOrderRequest {
  productId: string;
  buyerName: string;
  quantityKg: number;
}

export interface CreateOrderResponse {
  order_id: string;
  product_name: string;
  quantity_kg: number;
  /** Server-computed payable amount for this order; the only trusted total. */
  total_price: number;
  status: string;
  traceability_code: string | null;
}

export interface OrderListEntry {
  id: string;
  product_name: string;
  buyer_name: string;
  seller_id: string;
  quantity_kg: number;
  total_price: number;
  status: string;
  created_at: string;
}

export interface OrderListResponse {
  orders: OrderListEntry[];
  count: number;
}

export interface OrderTimelineResponse {
  order_id: string;
  order_number: string;
  current_status: string;
  timeline: Array<{
    timestamp: string;
    status: string;
    title: string;
    description: string;
  }>;
}

/** Why a marketplace request did not produce data. Drives the real UI states. */
export type ApiFailureKind = 'auth' | 'offline' | 'server' | 'not-found';

export function isApiFailure(
  result: ApiResult<unknown>,
): result is Extract<ApiResult<unknown>, { ok: false }> {
  return !result.ok;
}

/** `status === 0` is the client-side transport failure reported by `client.ts`. */
export function classifyApiFailure(status: number): ApiFailureKind {
  if (status === 0) return 'offline';
  if (status === 401 || status === 403) return 'auth';
  if (status === 404) return 'not-found';
  return 'server';
}

export function isAuthFailure(result: ApiResult<unknown>): boolean {
  return isApiFailure(result) && classifyApiFailure(result.status) === 'auth';
}

export function isOfflineFailure(result: ApiResult<unknown>): boolean {
  return isApiFailure(result) && classifyApiFailure(result.status) === 'offline';
}

export const CART_SOURCE = `${MARKETPLACE_BASE}/cart`;
export const ORDERS_SOURCE = `${MARKETPLACE_BASE}/orders`;

export function getCart(): Promise<ApiResult<CartResponse>> {
  return apiGet<CartResponse>(CART_SOURCE);
}

export function addToCart(items: AddToCartItem[]): Promise<ApiResult<CartResponse>> {
  return apiPost<CartResponse>(
    CART_SOURCE,
    { items: items.map((item) => ({ product_id: item.productId, quantity: item.quantity })) },
    { headers: { 'Idempotency-Key': createIdempotencyKey() } },
  );
}

export function updateCartItem(
  productId: string,
  quantity: number,
): Promise<ApiResult<CartResponse>> {
  return apiPatch<CartResponse>(`${CART_SOURCE}/${encodeURIComponent(productId)}`, { quantity });
}

export function removeFromCart(productId: string): Promise<ApiResult<{ removed: string }>> {
  return apiDelete<{ removed: string }>(`${CART_SOURCE}/${encodeURIComponent(productId)}`);
}

/**
 * Creates one order per real cart line. `total_price` comes back from the server
 * and is the only amount the payment step is allowed to charge.
 */
export function createOrder(request: CreateOrderRequest): Promise<ApiResult<CreateOrderResponse>> {
  return apiPost<CreateOrderResponse>(
    ORDERS_SOURCE,
    {
      product_id: request.productId,
      buyer_name: request.buyerName,
      quantity_kg: request.quantityKg,
    },
    { headers: { 'Idempotency-Key': createIdempotencyKey() } },
  );
}

export function listOrders(status?: string): Promise<ApiResult<OrderListResponse>> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiGet<OrderListResponse>(`${ORDERS_SOURCE}${query}`);
}

export function getOrderTimeline(orderId: string): Promise<ApiResult<OrderTimelineResponse>> {
  return apiGet<OrderTimelineResponse>(`${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/track`);
}
