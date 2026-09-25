import { type ApiResult, apiGet, apiPost, createIdempotencyKey } from './client';

const MARKETPLACE_BASE = '/api/v1/marketplace';

export interface CreatePaymentRequest {
  orderId: string;
  amount: number;
  paymentMethod: 'ecowallet' | 'bank' | 'card';
  description?: string;
}

export interface PaymentResponse {
  id?: string;
  payment_id?: string;
  order_id?: string;
  status?: string;
  escrow_status?: string;
  [key: string]: unknown;
}

export interface EscrowStatusResponse {
  payment_id: string;
  payment_status: string;
  escrow_status: string;
  entries: Array<{
    id: string;
    entry_type: string;
    amount?: number | null;
    created_at?: string;
  }>;
}

export interface EscrowTransitionResponse {
  ok?: boolean;
  order_id: string;
  escrow_id?: string;
  state: string;
  status?: string;
  settled_at?: string;
  completed_at?: string;
  remaining_seconds?: number | null;
}

function idempotentPost<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return apiPost<T>(path, body, {
    headers: { 'Idempotency-Key': createIdempotencyKey() },
  });
}

export function createPayment(request: CreatePaymentRequest): Promise<ApiResult<PaymentResponse>> {
  return idempotentPost<PaymentResponse>(`${MARKETPLACE_BASE}/payments`, {
    order_id: request.orderId,
    amount: request.amount,
    payment_method: request.paymentMethod,
    description: request.description ?? '',
  });
}

export function confirmPayment(
  paymentId: string,
  refId?: string,
): Promise<ApiResult<PaymentResponse>> {
  return idempotentPost<PaymentResponse>(`${MARKETPLACE_BASE}/payments/${paymentId}/confirm`, {
    ref_id: refId ?? '',
  });
}

export function getEscrowStatus(paymentId: string): Promise<ApiResult<EscrowStatusResponse>> {
  return apiGet<EscrowStatusResponse>(`${MARKETPLACE_BASE}/payments/${paymentId}/escrow`);
}

export function openDispute(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(`${MARKETPLACE_BASE}/orders/${orderId}/dispute`);
}

export function settleOrder(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(`${MARKETPLACE_BASE}/orders/${orderId}/settle`);
}

export function completeOrder(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(`${MARKETPLACE_BASE}/orders/${orderId}/complete`);
}
