/**
 * useCryptoWallets Hook
 * ======================
 * Fetches wallet data with React Query.
 *
 * In production, this would call a real API endpoint.
 * For demo, returns static INITIAL_WALLETS with simulated latency.
 *
 * @module features/crypto-payment/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { WalletInfo } from '../types';
import { INITIAL_WALLETS } from '../constants/wallets';

const QUERY_KEY = ['crypto-wallets'];

/** Simulated API latency (ms) */
const SIMULATED_LATENCY_MS = 300;

/**
 * Fetch wallets (simulated API call)
 */
async function fetchWallets(): Promise<WalletInfo[]> {
  // Simulate network latency
  await new Promise((resolve) => setTimeout(resolve, SIMULATED_LATENCY_MS));
  return INITIAL_WALLETS;
}

export function useCryptoWallets() {
  const query = useQuery<WalletInfo[], Error>({
    queryKey: QUERY_KEY,
    queryFn: fetchWallets,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  return {
    wallets: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
