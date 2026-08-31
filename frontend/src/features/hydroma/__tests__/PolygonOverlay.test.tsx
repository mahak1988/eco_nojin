/**
 * PolygonOverlay Tests
 * =====================
 * Unit tests for PolygonOverlay component.
 */

import { describe, it, expect } from 'vitest';
import { PolygonOverlay } from '../components/canvas';
import type { PolygonOverlayProps } from '../components/canvas/PolygonOverlay';
import type { TerrainData, Polygon } from '../types';

describe('PolygonOverlay Component', () => {
  describe('Exports', () => {
    it('should export PolygonOverlay as a function', () => {
      expect(typeof PolygonOverlay).toBe('function');
    });
  });

  describe('Props Interface', () => {
    it('should accept empty arrays', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const props: PolygonOverlayProps = {
        polygons: [],
        data: terrain,
        currentDrawing: [],
      };

      expect(props.polygons).toEqual([]);
      expect(props.currentDrawing).toEqual([]);
    });

    it('should accept multiple polygons', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const polygons: Polygon[] = [
        {
          id: 'poly-1',
          points: [
            { x: 0, y: 0 },
            { x: 10, y: 0 },
            { x: 10, y: 10 },
          ],
          name: 'Area 1',
          color: '#10b981',
          area: 50,
        },
        {
          id: 'poly-2',
          points: [
            { x: -5, y: -5 },
            { x: 5, y: -5 },
            { x: 0, y: 5 },
          ],
          name: 'Area 2',
          color: '#f59e0b',
          area: 25,
        },
      ];

      const props: PolygonOverlayProps = {
        polygons,
        data: terrain,
        currentDrawing: [],
      };

      expect(props.polygons).toHaveLength(2);
    });

    it('should handle in-progress drawing', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const props: PolygonOverlayProps = {
        polygons: [],
        data: terrain,
        currentDrawing: [
          { x: 0, y: 0 },
          { x: 5, y: 5 },
          { x: -3, y: 7 },
        ],
      };

      expect(props.currentDrawing).toHaveLength(3);
    });

    it('should handle polygons with area information', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const polygon: Polygon = {
        id: 'poly-1',
        points: [
          { x: 0, y: 0 },
          { x: 100, y: 0 },
          { x: 100, y: 100 },
          { x: 0, y: 100 },
        ],
        name: 'Large Area',
        color: '#3b82f6',
        area: 10000,
      };

      const props: PolygonOverlayProps = {
        polygons: [polygon],
        data: terrain,
        currentDrawing: [],
      };

      expect(props.polygons[0].area).toBe(10000);
    });
  });
});
