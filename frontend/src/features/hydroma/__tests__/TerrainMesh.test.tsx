/**
 * TerrainMesh Tests
 * ==================
 * Unit tests for TerrainMesh component.
 *
 * Testing strategy:
 * - Component export validation
 * - Props interface validation
 * - Type safety verification
 *
 * Note: Full rendering tests require WebGL environment (Playwright).
 * Component logic is validated via TypeScript compiler.
 */

import { describe, it, expect, vi } from 'vitest';
import { TerrainMesh, TerrainMeshErrorBoundary } from '../components/canvas';
import type { TerrainMeshProps } from '../components/canvas/TerrainMesh';
import type { TerrainData, LayerType } from '../types';

describe('TerrainMesh Component', () => {
  describe('Exports', () => {
    it('should export TerrainMesh as a function', () => {
      expect(typeof TerrainMesh).toBe('function');
    });

    it('should export TerrainMeshErrorBoundary', () => {
      expect(TerrainMeshErrorBoundary).toBeDefined();
      expect(typeof TerrainMeshErrorBoundary).toBe('function');
    });
  });

  describe('Props Interface', () => {
    it('should accept minimal required props', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const props: TerrainMeshProps = { data: terrain };
      expect(props.data).toBe(terrain);
      expect(props.data.width).toBe(10);
    });

    it('should accept all optional props', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const handleClick = vi.fn();
      const props: TerrainMeshProps = {
        data: terrain,
        onTerrainClick: handleClick,
        visible: true,
        opacity: 0.8,
        layer: 'surface',
        map: null,
      };

      expect(props.visible).toBe(true);
      expect(props.opacity).toBe(0.8);
      expect(props.layer).toBe('surface');
      expect(props.map).toBeNull();
      expect(props.onTerrainClick).toBe(handleClick);
    });

    it('should accept all layer types', () => {
      const validLayers: LayerType[] = [
        'surface',
        'soil',
        'bedrock',
        'ndvi',
        'moisture',
        'roots',
        'groundwater',
      ];

      validLayers.forEach((layer) => {
        expect([
          'surface',
          'soil',
          'bedrock',
          'ndvi',
          'moisture',
          'roots',
          'groundwater',
        ]).toContain(layer);
      });
    });
  });
});

describe('TerrainMeshErrorBoundary', () => {
  it('should be a valid class component', () => {
    expect(TerrainMeshErrorBoundary.prototype).toBeDefined();
    expect(typeof TerrainMeshErrorBoundary.prototype.render).toBe('function');
  });

  it('should have static getDerivedStateFromError', () => {
    expect(typeof TerrainMeshErrorBoundary.getDerivedStateFromError).toBe('function');
  });

  it('should return error state from getDerivedStateFromError', () => {
    const error = new Error('Test error');
    const state = TerrainMeshErrorBoundary.getDerivedStateFromError(error);
    expect(state.hasError).toBe(true);
    expect(state.error).toBe(error);
  });
});
