/**
 * EcoWallet API Functions
 * ========================
 * API client for EcoWallet endpoints.
 *
 * All functions return typed responses and handle errors properly.
 * Used by React Query hooks.
 *
 * @module features/eco-wallet/api
 */

import type {
  WalletStats,
  EarningOption,
  RedemptionOption,
} from '../types';
import { ENDPOINTS } from '../constants/config';

/**
 * Get authorization headers with token from localStorage
 */
function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Normalize API response (handles array/object variations)
 */
function normalizeOptions<T>(
  data: unknown
): T[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    const obj = data as { options?: T[]; items?: T[] };
    return obj.options || obj.items || [];
  }
  return [];
}

/**
 * Fetch wallet statistics
 */
export async function fetchWalletStats(): Promise<WalletStats> {
  const response = await fetch(ENDPOINTS.stats, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch wallet stats: ${response.statusText}`);
  }

  return response.json() as Promise<WalletStats>;
}

/**
 * Fetch earning options
 */
export async function fetchEarningOptions(): Promise<EarningOption[]> {
  const response = await fetch(ENDPOINTS.earningOptions, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch earning options: ${response.statusText}`);
  }

  const data = await response.json();
  return normalizeOptions<EarningOption>(data);
}

/**
 * Fetch redemption options
 */
export async function fetchRedemptionOptions(): Promise<RedemptionOption[]> {
  const response = await fetch(ENDPOINTS.redemptionOptions, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch redemption options: ${response.statusText}`
    );
  }

  const data = await response.json();
  return normalizeOptions<RedemptionOption>(data);
}
