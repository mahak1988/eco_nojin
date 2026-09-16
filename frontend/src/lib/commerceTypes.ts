/** Commerce shared TypeScript types. */

export type OrderStatus =
  | 'draft'
  | 'reserved'
  | 'paid'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'settled'
  | 'cancelled'
  | 'refunded';

export type PaymentStatus =
  | 'pending'
  | 'authorized'
  | 'paid'
  | 'failed'
  | 'refunded'
  | 'partial_refund';

export interface OrderItem {
  id: string;
  order_id: string;
  sku_id: number | null;
  sku_code: string;
  name: string;
  quantity: string;
  unit_price: string;
  line_total: string;
  warehouse_id: number | null;
  reservation_id: number | null;
  fulfilled_qty: string;
  notes: string | null;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  buyer_id: string;
  seller_id: string | null;
  status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: string;
  platform_fee: string;
  landscape_fee: string;
  total: string;
  currency: string;
  shipping_address: Record<string, unknown> | null;
  tracking_code: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  paid_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  idempotency_key: string | null;
  version: number;
  created_at: string;
  updated_at: string | null;
  items: OrderItem[];
  allowed_transitions: OrderStatus[];
}

export interface PaymentIntent {
  id: string;
  order_id: string;
  buyer_id: string;
  provider: string;
  amount: string;
  currency: string;
  status: string;
  provider_reference: string | null;
  payment_metadata: Record<string, unknown> | null;
  created_at: string;
  confirmed_at: string | null;
  cancelled_at: string | null;
  failure_reason: string | null;
}

export interface Settlement {
  id: string;
  order_id: string;
  seller_id: string;
  amount: string;
  currency: string;
  status: string;
  created_at: string;
}

export interface OrderCreateRequest {
  items: Array<{
    sku_code: string;
    quantity: string;
    unit_price?: string;
    warehouse_id?: number | null;
  }>;
  shipping_address?: Record<string, unknown> | null;
  idempotency_key?: string | null;
}

export interface OrderResponse {
  order_id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: string;
  platform_fee: string;
  landscape_fee: string;
  total: string;
  items: Array<{
    sku_code: string;
    quantity: string;
    unit_price: string;
  }>;
  allowed_transitions: OrderStatus[];
}
