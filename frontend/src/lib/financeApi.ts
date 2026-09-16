/** Finance API client — ledger, wallet, payments, reconciliation.
 * Follows existing hydromaApi.ts / marketplaceApi.ts patterns.
 */

import { getApiBase } from './api';
import type {
  Account,
  JournalEntry,
  EarnRequest,
  RedeemRequest,
  PaymentIntent,
  ReconciliationResult,
  IdempotencyKey,
  WalletState,
  WalletStats,
} from './financeTypes';

const apiBase = getApiBase();

async function financeFetch<T>(
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
    throw new Error((detail as { detail?: string }).detail || `finance_error_${res.status}`);
  }
  return res.json() as T;
}

// --- Accounts ---

export async function fetchAccounts(
  asset?: string,
  isActive?: boolean,
): Promise<Account[]> {
  const params = new URLSearchParams();
  if (asset) params.set('asset', asset);
  if (isActive !== undefined) params.set('is_active', String(isActive));
  const qs = params.toString();
  return financeFetch<Account[]>(`/api/v1/finance/accounts${qs ? `?${qs}` : ''}`);
}

export async function createAccount(body: {
  code: string;
  name: string;
  type: string;
  asset?: string | null;
  currency?: string;
  parent_id?: number | null;
}): Promise<Account> {
  return financeFetch<Account>('/api/v1/finance/accounts', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// --- Ledger ---

export async function fetchJournalEntries(params?: {
  account_id?: string;
  asset?: string;
  limit?: number;
}): Promise<JournalEntry[]> {
  const qs = new URLSearchParams();
  if (params?.account_id) qs.set('account_id', params.account_id);
  if (params?.asset) qs.set('asset', params.asset);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  return financeFetch<JournalEntry[]>(
    `/api/v1/finance/ledger/entries${q ? `?${q}` : ''}`,
  );
}

export async function fetchAccountBalance(
  accountId: string,
  asset?: string,
): Promise<{ account_id: string; asset: string; balance: string }> {
  const params = new URLSearchParams();
  if (asset) params.set('asset', asset);
  const qs = params.toString();
  return financeFetch(`/api/v1/finance/ledger/accounts/${accountId}/balance${qs ? `?${qs}` : ''}`);
}

// --- Wallet ---

export async function fetchWallet(): Promise<WalletState> {
  return financeFetch<WalletState>('/api/v1/finance/wallet');
}

export async function earnTokens(body: EarnRequest): Promise<{ amount_earned: string; new_balance: string; category: string }> {
  return financeFetch('/api/v1/finance/wallet/earn', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function redeemTokens(body: RedeemRequest): Promise<{ amount_redeemed: string; new_balance: string; category: string }> {
  return financeFetch('/api/v1/finance/wallet/redeem', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchWalletStats(): Promise<WalletStats> {
  return financeFetch<WalletStats>('/api/v1/finance/wallet/stats');
}

// --- Payment Intents ---

export async function createPaymentIntent(body: {
  amount: string;
  currency?: string;
  order_id: string;
  provider?: string;
  metadata?: Record<string, unknown>;
}): Promise<PaymentIntent> {
  return financeFetch<PaymentIntent>('/api/v1/finance/payments/intent', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// --- Reconciliation ---

export async function reconcileWalletLedger(): Promise<ReconciliationResult> {
  return financeFetch<ReconciliationResult>('/api/v1/finance/reconciliation/wallet-ledger', {
    method: 'POST',
  });
}

export async function fullReconciliation(): Promise<ReconciliationResult> {
  return financeFetch<ReconciliationResult>('/api/v1/finance/reconciliation/full', {
    method: 'POST',
  });
}

// --- Idempotency Keys ---

export async function fetchIdempotencyKeys(params?: {
  user_id?: string;
  status?: string;
  limit?: number;
}): Promise<IdempotencyKey[]> {
  const qs = new URLSearchParams();
  if (params?.user_id) qs.set('user_id', params.user_id);
  if (params?.status) qs.set('status', params.status);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  return financeFetch<IdempotencyKey[]>(
    `/api/v1/finance/idempotency/keys${q ? `?${q}` : ''}`,
  );
}

