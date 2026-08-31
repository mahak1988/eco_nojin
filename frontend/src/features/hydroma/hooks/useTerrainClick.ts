/**
 * useTerrainClick Hook
 * =====================
 * Handles terrain click events based on current tool mode.
 *
 * Tool Modes:
 * - 'orbit': No action (camera control only)
 * - 'data-plot': Sample terrain data and add plot
 * - 'draw-polygon': Add point to current drawing
 * - 'place-op': Place engineering operation + trigger RUSLE
 *
 * @module features/hydroma/hooks/useTerrainClick
 */

import { useCallback } from 'react';
import * as THREE from 'three';
import type { ToolMode, TerrainData, DataPlot, PlacedOp, SiteMeta } from '../types';
import { ENGINEERING_OPS, isErosionReducingOp } from '../constants';
import { samplePlotData } from '../../../components/farmsim/SceneExtras';
import { useHydromaStore } from '../store';

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

interface UseTerrainClickOptions {
  /** Terrain data */
  terrain: TerrainData | null;
  /** Site metadata (for RUSLE API calls) */
  siteMeta: SiteMeta | null;
  /** Persian language flag */
  isFa: boolean;
  /** Callback to update erosion effect */
  onErosionEffect: (effect: any) => void;
  /** Callback to update terrain data (for erosion modification) */
  onTerrainUpdate: (updater: (prev: TerrainData | null) => TerrainData | null) => void;
}

// ─────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────

export function useTerrainClick({
  terrain,
  siteMeta,
  isFa,
  onErosionEffect,
  onTerrainUpdate,
}: UseTerrainClickOptions) {
  const { toolMode, selectedOpType, addPlot, addDrawingPoint, addPlacedOp, setLastClickInfo } =
    useHydromaStore();

  const handleTerrainClick = useCallback(
    (point: THREE.Vector3) => {
      if (!terrain) return;

      const x = point.x;
      const y = point.z;

      setLastClickInfo(`Click at (${x.toFixed(2)}, ${y.toFixed(2)})`);

      // ── Data Plot Mode ───────────────────────────────────
      if (toolMode === 'data-plot') {
        // @ts-expect-error TerrainData type mismatch between lib/terrainGenerator and hydroma.types
        const data = samplePlotData(terrain, x, y);
        const plot: DataPlot = {
          id: 'p' + Date.now(),
          center: [x, y],
          size: [6, 5],
          data,
        };
        addPlot(plot);
        return;
      }

      // ── Draw Polygon Mode ────────────────────────────────
      if (toolMode === 'draw-polygon') {
        addDrawingPoint({ x, y });
        return;
      }

      // ── Place Operation Mode ─────────────────────────────
      if (toolMode === 'place-op' && selectedOpType) {
        const op = ENGINEERING_OPS.find((o) => o.id === selectedOpType);
        if (!op) return;

        const newOp: PlacedOp = {
          id: `op-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          type: op.id,
          x,
          y,
          label: isFa ? op.fa : op.name,
        };

        // Trigger RUSLE for erosion-reducing operations
        if (isErosionReducingOp(selectedOpType) && siteMeta?.siteId) {
          void (async () => {
            try {
              const res = await fetch(
                `/api/v1/elevation/erosion-effect/${siteMeta.siteId}?op_type=${selectedOpType}`
              );
              if (!res.ok) return;

              const d = await res.json();
              onErosionEffect(d);

              // Apply erosion reduction to terrain
              const ratio = d.A_before_t_ha_yr > 0 ? d.A_after_t_ha_yr / d.A_before_t_ha_yr : 1;

              onTerrainUpdate((prev) =>
                prev
                  ? {
                      ...prev,
                      erosion: (prev?.erosion ?? []).map((row) => row.map((v) => +(v * ratio).toFixed(3))),
                    }
                  : prev
              );
            } catch {
              // Silent fail - sidebar shows demError for real failures
            }
          })();
        }

        addPlacedOp(newOp);
      }
    },
    [
      terrain,
      toolMode,
      selectedOpType,
      siteMeta,
      isFa,
      addPlot,
      addDrawingPoint,
      addPlacedOp,
      setLastClickInfo,
      onErosionEffect,
      onTerrainUpdate,
    ]
  );

  return { handleTerrainClick };
}
