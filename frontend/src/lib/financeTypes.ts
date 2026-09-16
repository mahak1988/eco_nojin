/** Finance shared TypeScript types. */

export type AccountType = 'asset' | 'liability' | 'equity' | 'income' | 'expense';

export interface Account {
  id: number;
  code: string;
  name: string;
  type: AccountType;
  asset: string | null;
  currency: string;
  is_active: boolean;
}

export interface JournalEntry {
  id: number;
  batch_id: number | null;
  account_id: string;
  entry_type: 'debit' | 'credit';
  asset: string;
  amount: string;
  description: string | null;
  created_at: string | null;
}

export interface JournalBatch {
  id: number;
  batch_number: string;
  batch_date: string;
  reference_type: string | null;
  reference_id: string | null;
  description: string | null;
  created_by: string | null;
  created_at: string | null;
  posted_at: string | null;
  is_posted: boolean;
  entries: JournalEntry[];
}

export interface WalletState {
  user_id: string;
  balance: string;
  total_earned: string;
  total_redeemed: string;
  is_active: boolean;
}

export type PaymentProviderName = 'stripe' | 'wallet' | 'cod' | 'bank_transfer';

export interface PaymentIntent {
  id: string;
  order_id: string;
  provider: PaymentProviderName;
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

export interface ReconciliationResult {
  checked_at: string;
  total_checked: number;
  discrepancies_count: number;
  discrepancies: Record<string, unknown>[];
  overall_ok: boolean;
}

export interface IdempotencyKey {
  key: string;
  user_id: string;
  route: string;
  request_hash: string;
  status: 'pending' | 'completed' | 'failed';
  response_code: number | null;
  response_body: Record<string, unknown> | null;
  created_at: string;
  expires_at: string;
}

export interface WalletStats {
  total_wallets: number;
  total_tokens_issued: number;
  total_tokens_earned: number;
  total_tokens_redeemed: number;
}

export type EarnCategory =
  | 'tree_planting'
  | 'soil_health'
  | 'water_saving'
  | 'carbon_credit'
  | 'education'
  | 'community';

export type RedeemCategory = 'consultation' | 'satellite_report' | 'marketplace_discount';

export interface EarnRequest {
  category: EarnCategory;
  quantity: string;
  idempotency_key?: string | null;
  reference_id?: string | null;
}

export interface RedeemRequest {
  category: RedeemCategory;
  idempotency_key?: string | null;
  reference_id?: string | null;
}
