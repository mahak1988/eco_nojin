import { z } from 'zod';
import { type ApiResult, apiGet, apiPost, createIdempotencyKey } from './client';

const MARKETPLACE_BASE = '/api/v1/marketplace';

/**
 * The gateway only accepts these three payment gateways
 * (`services/marketplace/payments_service.py::VALID_GATEWAYS`). Offering any
 * other method would only produce a rejected request, so the UI is bound to
 * this list instead of an invented set of options.
 */
export const PAYMENT_GATEWAYS = ['zarinpal', 'bank', 'international'] as const;
export type PaymentGateway = (typeof PAYMENT_GATEWAYS)[number];

export function isPaymentGateway(value: string): value is PaymentGateway {
  return (PAYMENT_GATEWAYS as readonly string[]).includes(value);
}

/**
 * Gateways that answer `POST /payments` with a `redirect_url` the buyer has to
 * be sent to (`payments_service.py::PaymentGateways.create`). `bank` is absent
 * on purpose: it returns `redirect_url: null` and waits for a transfer
 * reference instead.
 */
export const REDIRECT_GATEWAYS = ['zarinpal', 'international'] as const;
export type RedirectGateway = (typeof REDIRECT_GATEWAYS)[number];

export function isRedirectGateway(value: PaymentGateway): value is RedirectGateway {
  return (REDIRECT_GATEWAYS as readonly string[]).includes(value);
}

/**
 * `PaymentConfirmRequest.ref_id` caps the bank tracking code at 120 characters
 * and a bank payment cannot be verified without one
 * (`payments_service.py::PaymentGateways.verify`).
 */
export const transactionKeySchema = z
  .string()
  .trim()
  .min(1, { message: 'the bank tracking code is required' })
  .max(120, { message: 'the bank tracking code is limited to 120 characters' });

export function isValidTransactionKey(value: string): boolean {
  return transactionKeySchema.safeParse(value).success;
}

export interface CreatePaymentRequest {
  orderId: string;
  /** Server-computed order total, never a client-side estimate. */
  amount: number;
  paymentMethod: PaymentGateway;
  description?: string;
}

export interface PaymentResponse {
  id: string;
  order_id: string;
  gateway: string;
  amount: number;
  currency: string;
  status: string;
  escrow_status: string;
  redirect_url: string | null;
  ref_id: string | null;
  created_at: string | null;
  bank_instructions?: Record<string, string> | null;
}

export interface PaymentConfirmResponse {
  payment: PaymentResponse;
  escrow: string;
  escrow_entries: EscrowEntry[];
}

export interface EscrowEntry {
  id: string;
  entry_type: string;
  amount: number | null;
  created_at?: string | null;
}

export interface EscrowStatusResponse {
  payment_id: string;
  payment_status: string;
  escrow_status: string;
  entries: EscrowEntry[];
}

export interface EscrowTransitionResponse {
  order_id: string;
  escrow_id: string;
  state: string;
  status?: string;
  amount?: number;
  settled_at?: string | null;
  completed_at?: string | null;
  dispute_deadline?: string | null;
  remaining_seconds?: number | null;
}

export const ESCROW_SOURCE = `${MARKETPLACE_BASE}/payments`;
export const ORDERS_SOURCE = `${MARKETPLACE_BASE}/orders`;

function idempotentPost<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return apiPost<T>(path, body, { headers: { 'Idempotency-Key': createIdempotencyKey() } });
}

export function createPayment(request: CreatePaymentRequest): Promise<ApiResult<PaymentResponse>> {
  return idempotentPost<PaymentResponse>(ESCROW_SOURCE, {
    order_id: request.orderId,
    amount: request.amount,
    payment_method: request.paymentMethod,
    description: request.description ?? '',
  });
}

/** Moves a verified payment into escrow hold. Bank transfers need the buyer ref id. */
export function confirmPayment(
  paymentId: string,
  refId?: string,
): Promise<ApiResult<PaymentConfirmResponse>> {
  return idempotentPost<PaymentConfirmResponse>(
    `${ESCROW_SOURCE}/${encodeURIComponent(paymentId)}/confirm`,
    { ref_id: refId ?? '' },
  );
}

export function getEscrowStatus(paymentId: string): Promise<ApiResult<EscrowStatusResponse>> {
  return apiGet<EscrowStatusResponse>(`${ESCROW_SOURCE}/${encodeURIComponent(paymentId)}/escrow`);
}

export function openDispute(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(
    `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/dispute`,
  );
}

export function settleOrder(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(
    `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/settle`,
  );
}

export function completeOrder(orderId: string): Promise<ApiResult<EscrowTransitionResponse>> {
  return idempotentPost<EscrowTransitionResponse>(
    `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/complete`,
  );
}

/** Total held in escrow, derived only from the real ledger entries. */
export function heldAmount(entries: EscrowEntry[]): number | null {
  const hold = entries
    .filter((entry) => entry.entry_type === 'hold')
    .reduce((sum, entry) => sum + (entry.amount ?? 0), 0);
  return entries.some((entry) => entry.entry_type === 'hold') ? hold : null;
}
