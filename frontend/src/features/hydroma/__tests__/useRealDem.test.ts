/**
 * useRealDem Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useRealDem } from '../hooks';

// Mock lib/demApi
vi.mock('../../../lib/demApi', () => ({
  fetchDemGrid: vi.fn(),
  buildRealTerrain: vi.fn(),
}));

describe('useRealDem Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should export hook as function', () => {
    expect(typeof useRealDem).toBe('function');
  });

  it('should return initial state', () => {
    const { result } = renderHook(() => useRealDem());

    expect(result.current.terrain).toBeNull();
    expect(result.current.siteMeta).toBeNull();
    expect(result.current.error).toBe('');
  });

  it('should expose loadSite function', () => {
    const { result } = renderHook(() => useRealDem());
    expect(typeof result.current.loadSite).toBe('function');
  });

  it('should have loading state', () => {
    const { result } = renderHook(() => useRealDem());
    expect(typeof result.current.loading).toBe('boolean');
  });
});
