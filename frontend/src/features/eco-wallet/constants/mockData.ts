/**
 * EcoWallet Mock Data
 * ====================
 * Deterministic mock data for transaction chart.
 *
 * Uses seeded random number generator for reproducible data.
 * This replaces Math.random() in render body.
 *
 * @module features/eco-wallet/constants
 */

import type { TransactionDataPoint, ChartConfig } from '../types';
import { CHART_CONFIG } from './config';

/**
 * Simple Linear Congruential Generator (LCG) for seeded random.
 *
 * @see https://en.wikipedia.org/wiki/Linear_congruential_generator
 */
function seededRandom(seed: number): () => number {
  let state = seed;
  return () => {
    // Numerical Recipes LCG parameters
    state = (state * 1664525 + 1013904223) % 2 ** 32;
    return state / 2 ** 32;
  };
}

/**
 * Generate deterministic transaction history for chart.
 *
 * @param config - Chart configuration
 * @param seed - Random seed (default: fixed seed for consistency)
 * @returns Array of daily transaction data points
 */
export function generateTransactionHistory(
  config: ChartConfig = CHART_CONFIG,
  seed: number = 42
): TransactionDataPoint[] {
  const random = seededRandom(seed);

  return Array.from({ length: config.days }, (_, i) => {
    const earningsRange =
      config.earningsRange.max - config.earningsRange.min;
    const redemptionsRange =
      config.redemptionsRange.max - config.redemptionsRange.min;

    return {
      day: `Day ${i + 1}`,
      earnings: Math.floor(
        config.earningsRange.min + random() * earningsRange
      ),
      redemptions: Math.floor(
        config.redemptionsRange.min + random() * redemptionsRange
      ),
    };
  });
}

/**
 * Default transaction history (pre-generated for consistency).
 */
export const DEFAULT_TRANSACTION_HISTORY: TransactionDataPoint[] =
  generateTransactionHistory();
