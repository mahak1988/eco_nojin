/**
 * EcoWallet Types
 * =================
 * Type definitions for EcoWallet dashboard.
 *
 * @module features/eco-wallet/types
 */

// ─────────────────────────────────────────────────────────────────────
// API Response Types
// ─────────────────────────────────────────────────────────────────────

/** Earning option from API */
export interface EarningOption {
  category: string;
  eco_amount: number;
  description: string;
}

/** Redemption option from API */
export interface RedemptionOption {
  category: string;
  eco_amount: number;
  description: string;
}

/** Wallet statistics from API */
export interface WalletStats {
  total_wallets?: number;
  active_wallets?: number;
  total_earnings?: number;
  total_redemptions?: number;
  pending?: number;
  total_transactions?: number;
}

// ─────────────────────────────────────────────────────────────────────
// Chart Data Types
// ─────────────────────────────────────────────────────────────────────

/** Single day data point for transaction chart */
export interface TransactionDataPoint {
  day: string;
  earnings: number;
  redemptions: number;
}

/** Chart configuration */
export interface ChartConfig {
  days: number;
  earningsRange: { min: number; max: number };
  redemptionsRange: { min: number; max: number };
}
