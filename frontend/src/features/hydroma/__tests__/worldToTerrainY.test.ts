/**
 * worldToTerrainY Tests
 * ======================
 * Unit tests for terrain coordinate conversion utilities.
 */

import { describe, it, expect } from 'vitest';
import { getTerrainYAtPoint, worldToGridPoint } from '../utils/worldToTerrainY';
import type { TerrainData } from '../types';

describe('worldToTerrainY utilities', () => {
  const createTerrain = (width = 10, height = 10): TerrainData => ({
    width,
    height,
    elevation: Array(height)
      .fill(0)
      .map(() => Array(width).fill(50)),
    moisture: Array(height)
      .fill(0)
      .map(() => Array(width).fill(0.5)),
    minElevation: 0,
    maxElevation: 100,
  });

  describe('getTerrainYAtPoint', () => {
    it('should calculate Y position at center', () => {
      const terrain = createTerrain();
      const y = getTerrainYAtPoint(terrain, 0, 0);
      expect(typeof y).toBe('number');
      expect(y).toBeGreaterThanOrEqual(0);
    });

    it('should apply offset', () => {
      const terrain = createTerrain();
      const yWithoutOffset = getTerrainYAtPoint(terrain, 0, 0, 0);
      const yWithOffset = getTerrainYAtPoint(terrain, 0, 0, 2);
      expect(yWithOffset - yWithoutOffset).toBeCloseTo(2, 5);
    });

    it('should handle edge coordinates', () => {
      const terrain = createTerrain();
      // Far outside world bounds - should still return valid Y
      const y = getTerrainYAtPoint(terrain, 100, 100);
      expect(typeof y).toBe('number');
      expect(isNaN(y)).toBe(false);
    });
  });

  describe('worldToGridPoint', () => {
    it('should convert world to grid coordinates', () => {
      const terrain = createTerrain();
      const result = worldToGridPoint(0, 0, terrain);
      expect(result.gridX).toBeGreaterThanOrEqual(0);
      expect(result.gridX).toBeLessThan(terrain.width);
      expect(result.gridY).toBeGreaterThanOrEqual(0);
      expect(result.gridY).toBeLessThan(terrain.height);
    });

    it('should clamp to valid grid range', () => {
      const terrain = createTerrain(10, 10);
      // Outside bounds
      const result = worldToGridPoint(1000, 1000, terrain);
      expect(result.gridX).toBeLessThan(terrain.width);
      expect(result.gridY).toBeLessThan(terrain.height);
      expect(result.gridX).toBeGreaterThanOrEqual(0);
      expect(result.gridY).toBeGreaterThanOrEqual(0);
    });
  });
});
