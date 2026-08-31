/**
 * useTerrainClick Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useTerrainClick } from '../hooks';
import type { TerrainData, SiteMeta } from '../types';

// Mock SceneExtras
vi.mock('../../../components/farmsim/SceneExtras', () => ({
  samplePlotData: vi.fn(() => ({
    moisture: 0.5,
    ndvi: 0.7,
    elevation: 150,
  })),
}));

// Mock store
vi.mock('../store', () => ({
  useHydromaStore: vi.fn(() => ({
    toolMode: 'orbit',
    selectedOpType: null,
    addPlot: vi.fn(),
    addDrawingPoint: vi.fn(),
    addPlacedOp: vi.fn(),
    setLastClickInfo: vi.fn(),
  })),
}));

describe('useTerrainClick Hook', () => {
  const createTerrain = (): TerrainData => ({
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
  });

  it('should export hook as function', () => {
    expect(typeof useTerrainClick).toBe('function');
  });

  it('should return handleTerrainClick function', () => {
    const { result } = renderHook(() =>
      useTerrainClick({
        terrain: createTerrain(),
        siteMeta: null,
        isFa: false,
        onErosionEffect: vi.fn(),
        onTerrainUpdate: vi.fn(),
      })
    );

    expect(typeof result.current.handleTerrainClick).toBe('function');
  });
});
