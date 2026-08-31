
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useRealDem } from '../useRealDem';

// Mock demApi
vi.mock('../../../lib/demApi', () => ({
  fetchDEM: vi.fn(),
}));

describe('useRealDem Hook', () => {
  it('should return initial state', () => {
    const { result } = renderHook(() => useRealDem({ lat: 40, lon: 50, size: 1000 }));

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.terrain).toBe(null);
  });

  it('should fetch DEM data on mount', async () => {
    const { fetchDEM } = await import('../../../lib/demApi');
    const mockDEM = {
      elevation: [[10, 20], [30, 40]],
      width: 2,
      height: 2,
      resolution: 30,
      bounds: { north: 40, south: 39, east: 51, west: 50 },
    };

    (fetchDEM as any).mockResolvedValueOnce(mockDEM);

    const { result } = renderHook(() => useRealDem({ lat: 40, lon: 50, size: 1000 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.terrain).toBeDefined();
    expect(result.current.error).toBe(null);
  });

  it('should handle fetch errors', async () => {
    const { fetchDEM } = await import('../../../lib/demApi');
    (fetchDEM as any).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useRealDem({ lat: 40, lon: 50, size: 1000 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeDefined();
    expect(result.current.terrain).toBe(null);
  });

  it('should retry fetch when coordinates change', async () => {
    const { fetchDEM } = await import('../../../lib/demApi');
    const mockDEM = {
      elevation: [[10]],
      width: 1,
      height: 1,
      resolution: 30,
      bounds: { north: 0, south: 0, east: 0, west: 0 },
    };

    (fetchDEM as any).mockResolvedValue(mockDEM);

    const { result, rerender } = renderHook(
      ({ lat, lon }) => useRealDem({ lat, lon, size: 1000 }),
      { initialProps: { lat: 40, lon: 50 } }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      rerender({ lat: 41, lon: 51 });
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetchDEM).toHaveBeenCalledTimes(2);
  });
});
