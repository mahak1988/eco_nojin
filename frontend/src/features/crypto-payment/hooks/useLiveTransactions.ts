/**
 * useLiveTransactions Hook
 * =========================
 * Manages live transaction feed with interval-based updates.
 *
 * Uses proper cleanup, abort handling, and state management
 * to replace the original setState-in-useEffect anti-pattern.
 *
 * @module features/crypto-payment/hooks
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { CryptoTransaction } from '../types';
import { generateMockTransaction } from '../utils/mockGenerator';
import { TX_UPDATE_INTERVAL_MS, MAX_TRANSACTIONS } from '../constants/config';

interface UseLiveTransactionsResult {
  transactions: CryptoTransaction[];
  lastUpdate: Date | null;
  isRunning: boolean;
  start: () => void;
  stop: () => void;
  refresh: () => void;
}

export function useLiveTransactions(
  autoStart: boolean = true,
  intervalMs: number = TX_UPDATE_INTERVAL_MS
): UseLiveTransactionsResult {
  const [transactions, setTransactions] = useState<CryptoTransaction[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isRunning, setIsRunning] = useState(autoStart);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seedRef = useRef<number>(Date.now());

  /** Generate a new transaction */
  const addTransaction = useCallback(() => {
    seedRef.current += 1;
    const newTx = generateMockTransaction(`tx-${Date.now()}`, seedRef.current);
    setTransactions((prev) => [newTx, ...prev].slice(0, MAX_TRANSACTIONS));
    setLastUpdate(new Date());
  }, []);

  /** Start the interval */
  const start = useCallback(() => {
    setIsRunning(true);
  }, []);

  /** Stop the interval */
  const stop = useCallback(() => {
    setIsRunning(false);
  }, []);

  /** Force refresh (generates new transaction immediately) */
  const refresh = useCallback(() => {
    addTransaction();
  }, [addTransaction]);

  // Setup and cleanup interval
  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(addTransaction, intervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, intervalMs, addTransaction]);

  return {
    transactions,
    lastUpdate,
    isRunning,
    start,
    stop,
    refresh,
  };
}
