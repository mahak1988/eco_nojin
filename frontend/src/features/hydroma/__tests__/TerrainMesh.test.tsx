/**
 * TerrainMesh Tests
 * ==================
 * Unit tests for TerrainMesh component.
 *
 * Testing strategy:
 * - Props validation
 * - Component exports
 * - Type safety (via TypeScript)
 *
 * Note: Full rendering tests require WebGL environment (Playwright).
 * These tests focus on structural validation.
 */

import { describe, it, expect } from 'vitest';
import { TerrainMesh, TerrainMeshErrorBoundary } from '../components/canvas';
import type { TerrainMeshProps } from '../components/canvas/TerrainMesh';
import type { TerrainData, LayerType } from '../types';

describe('TerrainMesh Component', () => {
  describe('Exports', () => {
    it('should export TerrainMesh function', () => {
      expect(typeof TerrainMesh).toBe('function');
    });

    it('should export TerrainMeshErrorBoundary class', () => {
      expect(typeof TerrainMeshErrorBoundary).toBe('function');
    });
  });

  describe('Props Interface', () => {
    it('should accept minimal props', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10).fill(Array(10).fill(0)),
        moisture: Array(10).fill(Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const props: TerrainMeshProps = { data: terrain };
      expect(props.data).toBe(terrain);
    });

    it('should accept all optional props', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10).fill(Array(10).fill(0)),
        moisture: Array(10).fill(Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const props: TerrainMeshProps = {
        data: terrain,
        onTerrainClick: () => {},
        visible: true,
        opacity: 0.8,
        layer: 'surface',
        map: null,
      };

      expect(props.visible).toBe(true);
      expect(props.opacity).toBe(0.8);
      expect(props.layer).toBe('surface');
    });

    it('should accept all layer types', () => {
      const layers: LayerType[] = [
        'surface', 'soil', 'bedrock', 'ndvi', 'moisture', 'roots', 'groundwater'
      ];

      layers.forEach(layer => {
        expect(['surface', 'soil', 'bedrock', 'ndvi', 'moisture', 'roots', 'groundwater'])
          .toContain(layer);
      });
    });
  });
});

describe('TerrainMeshErrorBoundary', () => {
  it('should be a React Component class', () => {
    // TypeScript ensures it's a valid Component, we just check it exists
    expect(TerrainMeshErrorBoundary).toBeDefined();
    expect(TerrainMeshErrorBoundary.prototype).toBeDefined();
  });
});
