/**
 * Crypto Payment Types
 * =====================
 * Type definitions for crypto payment widget.
 *
 * @module features/crypto-payment/types
 */

// ─────────────────────────────────────────────────────────────────────
// Core Enums
// ─────────────────────────────────────────────────────────────────────

/** Supported cryptocurrency types */
export type CryptoType = 'btc' | 'usdt' | 'eth';

/** Transaction status */
export type TransactionStatus = 'confirmed' | 'pending' | 'failed';

// ─────────────────────────────────────────────────────────────────────
// Interfaces
// ─────────────────────────────────────────────────────────────────────

/** Cryptocurrency transaction */
export interface CryptoTransaction {
  id: string;
  type: CryptoType;
  amount: number;
  usdValue: number;
  from: string;
  status: TransactionStatus;
  confirmations: number;
  timestamp: Date;
  txHash: string;
}

/** Wallet information */
export interface WalletInfo {
  address: string;
  balance: number;
  usdValue: number;
  type: CryptoType;
}

/** Wallet display metadata */
export interface WalletMeta {
  type: CryptoType;
  name: string;
  color: string;
  i18nKey: string;
}
