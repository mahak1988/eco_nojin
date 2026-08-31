/**
 * usePolygonDrawing Hook
 * =======================
 * Manages polygon drawing state and provides finish/clear actions.
 *
 * Features:
 * - Finish polygon with Shoelace formula area calculation
 * - Clear current drawing
 * - Validates minimum 3 points for polygon
 * - Converts world units to m² (2500 scale factor)
 * - Auto-assigns colors from palette
 *
 * @module features/hydroma/hooks/usePolygonDrawing
 */

import { useCallback } from 'react';
import type { Polygon } from '../types';
import { useHydromaStore } from '../store';

// ─────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────

/** Polygon color palette */
const POLYGON_COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4'];

/** Scale factor: world units → m² (20 units ≈ 1km → area factor) */
const AREA_SCALE_FACTOR = 2500;

// ─────────────────────────────────────────────────────────────────────
// Shoelace Formula
// ─────────────────────────────────────────────────────────────────────

/**
 * Calculate polygon area using Shoelace formula
 * @see https://en.wikipedia.org/wiki/Shoelace_formula
 */
function calculateShoelaceArea(points: Array<{ x: number; y: number }>): number {
  let area = 0;
  const n = points.length;

  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += points[i].x * points[j].y - points[j].x * points[i].y;
  }

  return Math.abs(area) / 2;
}

// ─────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────

export function usePolygonDrawing(isFa: boolean) {
  const { currentDrawing, polygons, addPolygon, clearDrawing } = useHydromaStore();

  /**
   * Finish current drawing and create polygon
   */
  const finishPolygon = useCallback(() => {
    if (currentDrawing.length < 3) return;

    // Calculate area in world units
    const worldArea = calculateShoelaceArea(currentDrawing);

    // Convert to m² (with scale factor)
    const area = worldArea * AREA_SCALE_FACTOR;

    // Get next color from palette (cycle)
    const color = POLYGON_COLORS[polygons.length % POLYGON_COLORS.length];

    const polygon: Polygon = {
      id: `poly-${Date.now()}`,
      points: currentDrawing,
      name: isFa ? `محدوده ${polygons.length + 1}` : `Area ${polygons.length + 1}`,
      color,
      area,
    };

    addPolygon(polygon);
  }, [currentDrawing, polygons.length, isFa, addPolygon]);

  /**
   * Clear current drawing without creating polygon
   */
  const cancel = useCallback(() => {
    clearDrawing();
  }, [clearDrawing]);

  return {
    finish: finishPolygon,
    cancel,
    pointCount: currentDrawing.length,
    canFinish: currentDrawing.length >= 3,
  };
}
