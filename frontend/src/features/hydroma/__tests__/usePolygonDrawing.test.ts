/**
 * usePolygonDrawing Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePolygonDrawing } from '../hooks';

// Mock store
vi.mock('../store', () => ({
  useHydromaStore: vi.fn(() => ({
    currentDrawing: [],
    polygons: [],
    addPolygon: vi.fn(),
    clearDrawing: vi.fn(),
  })),
}));

describe('usePolygonDrawing Hook', () => {
  it('should export hook as function', () => {
    expect(typeof usePolygonDrawing).toBe('function');
  });

  it('should return finish and cancel functions', () => {
    const { result } = renderHook(() => usePolygonDrawing(false));

    expect(typeof result.current.finish).toBe('function');
    expect(typeof result.current.cancel).toBe('function');
  });

  it('should report canFinish as false when no points', () => {
    const { result } = renderHook(() => usePolygonDrawing(false));
    expect(result.current.canFinish).toBe(false);
    expect(result.current.pointCount).toBe(0);
  });

  it('should support Persian locale', () => {
    const { result } = renderHook(() => usePolygonDrawing(true));
    expect(typeof result.current.finish).toBe('function');
  });
});
