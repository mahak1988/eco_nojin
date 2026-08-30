/**
 * World to Terrain Y Conversion Utility
 * ======================================
 * Shared utility for converting world coordinates to terrain Y position.
 *
 * This utility is used by:
 * - PlacedOpsMarkers (to place pins on terrain surface)
 * - PolygonOverlay (to draw polygons at terrain level)
 *
 * @module features/hydroma/utils/worldToTerrainY
 */

import type { TerrainData } from '../types';
import { HEIGHT_SCALE, worldToGrid } from '../../../lib/terrainGenerator';

/**
 * Calculate terrain Y position at a given world coordinate
 *
 * @param data - Terrain data with elevation grid
 * @param worldX - X coordinate in world space
 * @param worldY - Y coordinate in world space (Z in 3D)
 * @param offset - Vertical offset (default: 0, for placing objects above surface)
 * @returns Y position in world space
 */
export function getTerrainYAtPoint(
  data: TerrainData,
  worldX: number,
  worldY: number,
  offset: number = 0
): number {
  const gridX = Math.max(
    0,
    Math.min(data.width - 1, worldToGrid(worldX, data.width))
  );
  const gridY = Math.max(
    0,
    Math.min(data.height - 1, worldToGrid(worldY, data.height))
  );

  const elev = data.elevation[gridY]?.[gridX] ?? data.minElevation;
  const range = data.maxElevation - data.minElevation || 1;
  const norm = (elev - data.minElevation) / range;

  return norm * HEIGHT_SCALE + offset;
}

/**
 * Convert world coordinates to grid coordinates
 *
 * @param worldX - X coordinate in world space
 * @param worldY - Y coordinate in world space
 * @param data - Terrain data
 * @returns Grid coordinates clamped to valid range
 */
export function worldToGridPoint(
  worldX: number,
  worldY: number,
  data: TerrainData
): { gridX: number; gridY: number } {
  return {
    gridX: Math.max(
      0,
      Math.min(data.width - 1, worldToGrid(worldX, data.width))
    ),
    gridY: Math.max(
      0,
      Math.min(data.height - 1, worldToGrid(worldY, data.height))
    ),
  };
}
