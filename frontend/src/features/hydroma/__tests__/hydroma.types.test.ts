/**
 * HyDroMa Types Test
 * ==================
 * Simple test to verify type imports work correctly.
 */

import { describe, it, expect } from 'vitest';
import type {
  ViewMode,
  ToolMode,
  LayerType,
  TerrainData,
  PlacedOp,
  Polygon,
  HydromaState,
} from '../types';

describe('HyDroMa Types', () => {
  it('should accept valid ViewMode values', () => {
    const modes: ViewMode[] = ['3d', '2d-top', '2d-side', 'cross-section'];
    expect(modes).toHaveLength(4);
  });

  it('should accept valid ToolMode values', () => {
    const modes: ToolMode[] = ['orbit', 'draw-polygon', 'place-op', 'data-plot'];
    expect(modes).toHaveLength(4);
  });

  it('should accept valid LayerType values', () => {
    const layers: LayerType[] = [
      'surface', 'soil', 'bedrock', 'ndvi', 'moisture', 'roots', 'groundwater'
    ];
    expect(layers).toHaveLength(7);
  });

  it('should create valid TerrainData object', () => {
    const terrain: TerrainData = {
      width: 10,
      height: 10,
      elevation: Array(10).fill(Array(10).fill(0)),
      moisture: Array(10).fill(Array(10).fill(0.5)),
      minElevation: 0,
      maxElevation: 100,
    };
    expect(terrain.width).toBe(10);
    expect(terrain.elevation).toHaveLength(10);
  });

  it('should create valid PlacedOp object', () => {
    const op: PlacedOp = {
      id: 'op-1',
      type: 'gabion',
      x: 5,
      y: 10,
      label: 'Gabion Wall',
    };
    expect(op.id).toBe('op-1');
    expect(op.type).toBe('gabion');
  });

  it('should create valid Polygon object', () => {
    const polygon: Polygon = {
      id: 'poly-1',
      points: [
        { x: 0, y: 0 },
        { x: 10, y: 0 },
        { x: 10, y: 10 },
      ],
      name: 'Area 1',
      color: '#10b981',
      area: 100,
    };
    expect(polygon.points).toHaveLength(3);
    expect(polygon.area).toBe(100);
  });
});
