/**
 * useRealDem Hook
 * ===============
 * Loads real Digital Elevation Model (DEM) data from backend API.
 *
 * Features:
 * - Async DEM loading with error handling
 * - Automatic initialization with default site (SITE265)
 * - Returns terrain data and site metadata
 * - Manages loading/error states
 *
 * @module features/hydroma/hooks/useRealDem
 */

import { useState, useCallback, useEffect } from 'react';
import { fetchDemGrid, buildRealTerrain } from '../../../lib/demApi';
import type { DemGrid } from '../../../lib/demApi';
import type { TerrainData, SiteMeta } from '../types';

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

export interface UseRealDemResult {
  /** Current terrain data (null if not loaded) */
  terrain: TerrainData | null;
  /** Site metadata (lat, lon, siteId) */
  siteMeta: SiteMeta | null;
  /** Loading state */
  loading: boolean;
  /** Error message (empty string if no error) */
  error: string;
  /** Function to load a specific site */
  loadSite: (siteId: string) => Promise<void>;
  /** Last click info string */
  lastClickInfo: string;
}

// ─────────────────────────────────────────────────────────────────────
// Default Configuration
// ─────────────────────────────────────────────────────────────────────

/** Default site ID for auto-initialization */
const DEFAULT_SITE_ID = 'SITE265';

/** Whether to auto-load default site on mount */
const AUTO_INIT = true;

// ─────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────

export function useRealDem(): UseRealDemResult {
  const [terrain, setTerrain] = useState<TerrainData | null>(null);
  const [siteMeta, setSiteMeta] = useState<SiteMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastClickInfo, setLastClickInfo] = useState('');

  const loadSite = useCallback(async (siteId: string) => {
    setLoading(true);
    setError('');

    try {
      const dem: DemGrid = await fetchDemGrid(siteId);
      const built = buildRealTerrain(dem);

      setTerrain(built);
      setSiteMeta({
        lat: dem.lat,
        lon: dem.lon,
        siteId: dem.site_id,
      });

      const relief = (dem.max_elev - dem.min_elev).toFixed(0);
      setLastClickInfo(`Real DEM loaded: ${dem.site_id} relief=${relief}m`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      setLastClickInfo(`Error loading DEM: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-initialize with default site on mount
  useEffect(() => {
    if (AUTO_INIT && !terrain && !loading && !error) {
      void loadSite(DEFAULT_SITE_ID);
    }
  }, [terrain, loading, error, loadSite]);

  return {
    terrain,
    siteMeta,
    loading,
    error,
    loadSite,
    lastClickInfo,
  };
}
