/**
 * Crypto Payment Configuration
 * ==============================
 * Magic numbers extracted as named constants.
 *
 * @module features/crypto-payment/constants
 */

/** Live transaction update interval (ms) */
export const TX_UPDATE_INTERVAL_MS = 5000;

/** Maximum number of transactions to keep in memory */
export const MAX_TRANSACTIONS = 10;

/** Clipboard feedback duration (ms) */
export const CLIPBOARD_FEEDBACK_MS = 2000;

/** Minimum confirmations for "confirmed" status */
export const CONFIRMED_THRESHOLD = 6;

/** Minimum confirmations for "warning" status */
export const PENDING_THRESHOLD = 3;

/** Transaction status probability thresholds */
export const TX_STATUS_THRESHOLDS = {
  confirmedBelow: 0.3,
  pendingBelow: 0.5,
} as const;

/** Transaction amount range (for mock generation) */
export const TX_AMOUNT_RANGE = {
  min: 0,
  max: 1000,
} as const;

/** Transaction USD value range (for mock generation) */
export const TX_USD_RANGE = {
  min: 0,
  max: 10000,
} as const;
