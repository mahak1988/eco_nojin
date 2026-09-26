import { z } from 'zod';
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

/**
 * Order lifecycle the gateway models (`services/marketplace/models:OrderStatus`).
 * `GET /orders?status=` swallows an unknown value and returns every order, so
 * the client sends only these five and reports anything else as a bad request.
 */
export const ORDER_STATUSES = [
  'pending',
  'confirmed',
  'shipped',
  'delivered',
  'cancelled',
] as const;

export type OrderStatus = (typeof ORDER_STATUSES)[number];

export function isOrderStatus(value: string): value is OrderStatus {
  return (ORDER_STATUSES as readonly string[]).includes(value);
}

export function listOrders(status?: OrderStatus): Promise<ApiResult<OrderListResponse>> {
  if (status !== undefined && !isOrderStatus(status)) {
    return Promise.resolve({
      ok: false,
      error: `Unknown order status: ${status}`,
      status: 400,
    });
  }
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiGet<OrderListResponse>(`${ORDERS_SOURCE}${query}`);
}

/**
 * `GET /orders` carries no `response_model`, so an order read from it is
 * validated before its money field is trusted by a payment step
 * (`marketplace.py::list_orders` is the only order read the gateway exposes).
 */
const orderEntrySchema = z.object({
  id: z.string().min(1),
  product_name: z.string(),
  buyer_name: z.string(),
  seller_id: z.string().default(''),
  quantity_kg: z.number(),
  total_price: z.number(),
  status: z.string().min(1),
  created_at: z.string().min(1),
});

/**
 * Resolves one order through the only endpoint the gateway exposes for it.
 * A missing order is reported as `404` instead of an empty success, so a
 * checkout step can never continue with an order that does not exist.
 */
export async function getOrder(orderId: string): Promise<ApiResult<OrderListEntry>> {
  const result = await listOrders();
  if (!result.ok) return result;
  const match = result.data.orders.find((entry) => entry.id === orderId);
  if (!match) {
    return { ok: false, error: `Order ${orderId} is not in the gateway order list`, status: 404 };
  }
  const parsed = orderEntrySchema.safeParse(match);
  if (!parsed.success) {
    return {
      ok: false,
      error: `Order ${orderId} does not match the gateway order contract: ${parsed.error.issues
        .map((issue) => `${issue.path.join('.') || 'order'}: ${issue.message}`)
        .join('; ')}`,
      status: 502,
    };
  }
  return { ok: true, data: parsed.data, status: result.status };
}

export function getOrderTimeline(orderId: string): Promise<ApiResult<OrderTimelineResponse>> {
  return apiGet<OrderTimelineResponse>(`${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/track`);
}
