/**
 * useErosionEffect Hook
 * ======================
 * Manages erosion effect calculation via backend RUSLE API.
 *
 * Features:
 * - Fetches erosion before/after data
 * - Calculates reduction percentage
 * - Manages loading state
 * - Handles errors gracefully
 *
 * @module features/hydroma/hooks/useErosionEffect
 */

import { useState, useCallback } from 'react';
import type { ErosionEffect } from '../types';

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

export interface UseErosionEffectResult {
  /** Current erosion effect data */
  effect: ErosionEffect | null;
  /** Loading state */
  loading: boolean;
  /** Error message */
  error: string;
  /** Function to fetch erosion effect */
  fetchEffect: (siteId: string, opType: string) => Promise<void>;
  /** Clear current effect */
  clear: () => void;
}

// ─────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────

export function useErosionEffect(): UseErosionEffectResult {
  const [effect, setEffect] = useState<ErosionEffect | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchEffect = useCallback(
    async (siteId: string, opType: string) => {
      setLoading(true);
      setError('');

      try {
        const url = `/api/v1/elevation/erosion-effect/${siteId}?op_type=${opType}`;
        const res = await fetch(url);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        setEffect(data);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => {
    setEffect(null);
    setError('');
  }, []);

  return {
    effect,
    loading,
    error,
    fetchEffect,
    clear,
  };
}
