import { apiDelete, apiGet, apiPatch, apiPost, createIdempotencyKey } from './client';

const MARKETPLACE_BASE = '/api/v1/marketplace';

export interface CartLine {
  product_id: string;
  quantity: number;
  product_name?: string;
  producer_name?: string;
  price?: number;
  unit?: string;
  in_stock?: boolean;
}

export interface CartResponse {
  cart_id: string | null;
  items: CartLine[];
  total_items: number;
  subtotal?: number;
}

export interface CreateOrderRequest {
  productId: string;
  buyerName: string;
  quantityKg: number;
}

export interface CreateOrderResponse {
  order_id: string;
  product_name?: string;
  quantity_kg?: number;
  total_price?: number;
  status?: string;
  traceability_code?: string;
}

export function getCart(): Promise<import('./client').ApiResult<CartResponse>> {
  return apiGet<CartResponse>(`${MARKETPLACE_BASE}/cart`);
}

export function addToCart(
  items: Array<{ productId: string; quantity: number }>,
): Promise<import('./client').ApiResult<CartResponse>> {
  return apiPost<CartResponse>(
    `${MARKETPLACE_BASE}/cart`,
    { items: items.map((item) => ({ product_id: item.productId, quantity: item.quantity })) },
    {
      headers: { 'Idempotency-Key': createIdempotencyKey() },
    },
  );
}

export function updateCartItem(
  productId: string,
  quantity: number,
): Promise<import('./client').ApiResult<CartResponse>> {
  return apiPatch<CartResponse>(`${MARKETPLACE_BASE}/cart/${productId}`, { quantity });
}

export function removeFromCart(
  productId: string,
): Promise<import('./client').ApiResult<{ removed: string }>> {
  return apiDelete<{ removed: string }>(`${MARKETPLACE_BASE}/cart/${productId}`);
}

export function createOrder(
  request: CreateOrderRequest,
): Promise<import('./client').ApiResult<CreateOrderResponse>> {
  return apiPost<CreateOrderResponse>(
    `${MARKETPLACE_BASE}/orders`,
    {
      product_id: request.productId,
      buyer_name: request.buyerName,
      quantity_kg: request.quantityKg,
    },
    {
      headers: { 'Idempotency-Key': createIdempotencyKey() },
    },
  );
}
