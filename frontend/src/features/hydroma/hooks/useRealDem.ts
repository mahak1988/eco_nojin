/**
 * useRealDem Hook (Store-Based)
 * =============================
 * Loads real DEM data from API and syncs with Zustand store.
 *
 * This version uses the global store as source of truth,
 * ensuring all components see the same terrain/siteMeta state.
 *
 * @module features/hydroma/hooks/useRealDem
 */

import { useCallback, useEffect } from 'react';
import { fetchDemGrid, buildRealTerrain } from '../../../lib/demApi';
import type { DemGrid } from '../../../lib/demApi';
import { useHydromaStore } from '../store';

const DEFAULT_SITE_ID = 'SITE265';
const AUTO_INIT = true;

export interface UseRealDemResult {
  terrain: ReturnType<typeof useHydromaStore.getState>['terrain'];
  siteMeta: ReturnType<typeof useHydromaStore.getState>['siteMeta'];
  loading: boolean;
  error: string;
  loadSite: (siteId: string) => Promise<void>;
  lastClickInfo: string;
}

export function useRealDem(): UseRealDemResult {
  const terrain = useHydromaStore((s) => s.terrain);
  const siteMeta = useHydromaStore((s) => s.siteMeta);
  const demLoading = useHydromaStore((s) => s.demLoading);
  const demError = useHydromaStore((s) => s.demError);
  const lastClickInfo = useHydromaStore((s) => s.lastClickInfo);

  const setTerrain = useHydromaStore((s) => s.setTerrain);
  const setSiteMeta = useHydromaStore((s) => s.setSiteMeta);
  const setDemLoading = useHydromaStore((s) => s.setDemLoading);
  const setDemError = useHydromaStore((s) => s.setDemError);
  const setLastClickInfo = useHydromaStore((s) => s.setLastClickInfo);

  const loadSite = useCallback(
    async (siteId: string) => {
      setDemLoading(true);
      setDemError('');

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
        const msg = err instanceof Error ? err.message : String(err);
        setDemError(msg);
      } finally {
        setDemLoading(false);
      }
    },
    [setDemLoading, setDemError, setTerrain, setSiteMeta, setLastClickInfo]
  );

  useEffect(() => {
    if (AUTO_INIT && !terrain && !demLoading && !demError) {
      void loadSite(DEFAULT_SITE_ID);
    }
  }, [terrain, demLoading, demError, loadSite]);

  return {
    terrain,
    siteMeta,
    loading: demLoading,
    error: demError,
    loadSite,
    lastClickInfo,
  };
}
