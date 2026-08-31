import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

// Mock the demApi module before importing the hook
vi.mock('../../../lib/demApi', () => ({
  fetchDEM: vi.fn().mockResolvedValue({
    elevation: [[10, 20], [30, 40]],
    width: 2,
    height: 2,
    resolution: 30,
    bounds: { north: 40, south: 39, east: 51, west: 50 },
  }),
}));

// Import hook after mocking
import { useRealDem } from '../useRealDem';

describe('useRealDem Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    expect(useRealDem).toBeDefined();
    expect(typeof useRealDem).toBe('function');
  });

  it('should return a valid hook result', () => {
    const { result } = renderHook(() => useRealDem({ lat: 40, lon: 50, size: 1000 }));
    
    // Hook should return an object or value
    expect(result.current).toBeDefined();
  });

  it('should handle different coordinates', () => {
    const { result, rerender } = renderHook(
      ({ lat, lon }) => useRealDem({ lat, lon, size: 1000 }),
      { initialProps: { lat: 40, lon: 50 } }
    );

    expect(result.current).toBeDefined();

    // Rerender with new props
    rerender({ lat: 41, lon: 51 });
    expect(result.current).toBeDefined();
  });
});
