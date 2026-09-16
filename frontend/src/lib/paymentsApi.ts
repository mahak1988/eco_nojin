/** Bazargah payments API — multi-gateway (zarinpal | bank | international) + escrow. */

import { getApiBase } from './api';

const apiBase = getApiBase();

function idemKey(): string {
  return (crypto?.randomUUID?.() ?? `idem-${Date.now()}-${Math.random().toString(36).slice(2)}`);
}

async function payFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Idempotency-Key': idemKey(),
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydroma_token');
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `payment_error_${res.status}`);
  }
  return res.json() as T;
}

export type PaymentGateway = 'zarinpal' | 'bank' | 'international';

export interface PaymentDto {
  id: string;
  order_id: string;
  gateway: PaymentGateway;
  amount: number;
  currency: string;
  status: string;
  escrow_status: string;
  redirect_url: string | null;
  ref_id: string | null;
  bank_instructions?: { card_number: string; sheba: string; holder: string };
}

/** Step 1 — create the gateway payment (zarinpal returns a redirect_url). */
export function createPayment(payload: {
  order_id: string;
  amount: number;
  payment_method: PaymentGateway;
  description?: string;
}): Promise<PaymentDto> {
  return payFetch('/api/v1/marketplace/payments', { method: 'POST', body: JSON.stringify(payload) });
}

/** Step 2 — verify (bank tracking code / gateway ref) and hold in escrow. */
export function confirmPayment(paymentId: string, refId: string): Promise<{ payment: PaymentDto; escrow: string }> {
  return payFetch(`/api/v1/marketplace/payments/${paymentId}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ ref_id: refId }),
  });
}
