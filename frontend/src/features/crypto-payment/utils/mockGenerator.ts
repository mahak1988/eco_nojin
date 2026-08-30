/**
 * Mock Generator
 * ===============
 * Deterministic mock data generator for transactions.
 *
 * Uses a seed-based approach for testability while appearing random
 * in production. In a real app, this would be replaced with API calls.
 *
 * @module features/crypto-payment/utils
 */

import type { CryptoTransaction, CryptoType, TransactionStatus } from '../types';
import {
  TX_AMOUNT_RANGE,
  TX_USD_RANGE,
  TX_STATUS_THRESHOLDS,
} from '../constants/config';

const CRYPTO_TYPES: CryptoType[] = ['btc', 'usdt', 'eth'];

/**
 * Simple seeded random number generator (LCG algorithm).
 *
 * Uses Linear Congruential Generator for reproducible pseudo-random
 * sequences. Not cryptographically secure — only for UI mocks.
 *
 * @see https://en.wikipedia.org/wiki/Linear_congruential_generator
 */
function seededRandom(seed: number): number {
  // LCG parameters (Numerical Recipes)
  const a = 1664525;
  const c = 1013904223;
  const m = 2 ** 32;
  const nextSeed = (a * seed + c) % m;
  return nextSeed / m;
}

/**
 * Generate a hex string of specified length from a seed.
 */
function generateHexString(seed: number, length: number): string {
  let result = '';
  let currentSeed = seed;
  while (result.length < length) {
    currentSeed = (currentSeed * 1664525 + 1013904223) % 2 ** 32;
    result += Math.floor(seededRandom(currentSeed) * 16).toString(16);
  }
  return result.slice(0, length);
}

/**
 * Determine transaction status based on random value.
 */
function determineStatus(rand: number): TransactionStatus {
  if (rand < TX_STATUS_THRESHOLDS.confirmedBelow) return 'confirmed';
  if (rand < TX_STATUS_THRESHOLDS.pendingBelow) return 'pending';
  return 'failed';
}

/**
 * Generate a mock crypto transaction.
 *
 * @param id - Unique transaction ID
 * @param seed - Random seed (defaults to Date.now())
 */
export function generateMockTransaction(
  id: string,
  seed: number = Date.now()
): CryptoTransaction {
  const rand1 = seededRandom(seed);
  const rand2 = seededRandom(seed + 1);
  const rand3 = seededRandom(seed + 2);
  const rand4 = seededRandom(seed + 3);
  const rand5 = seededRandom(seed + 4);

  const type = CRYPTO_TYPES[Math.floor(rand1 * CRYPTO_TYPES.length)];
  const amount = TX_AMOUNT_RANGE.min + rand2 * (TX_AMOUNT_RANGE.max - TX_AMOUNT_RANGE.min);
  const usdValue = TX_USD_RANGE.min + rand3 * (TX_USD_RANGE.max - TX_USD_RANGE.min);
  const status = determineStatus(rand4);
  const confirmations = Math.floor(rand5 * 10);

  return {
    id,
    type,
    amount,
    usdValue,
    from: '0x' + generateHexString(seed + 5, 40), // Valid Ethereum address length
    status,
    confirmations,
    timestamp: new Date(),
    txHash: '0x' + generateHexString(seed + 6, 64), // Valid Ethereum tx hash
  };
}
