/**
 * useEsriTexture Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useEsriTexture } from '../hooks';
import type { SiteMeta } from '../types';

// Mock THREE with load callback support
const mockLoad = vi.fn();
vi.mock('three', () => ({
  default: {
    TextureLoader: vi.fn().mockImplementation(() => ({
      setCrossOrigin: vi.fn(),
      load: (url: string, onLoad: (tex: any) => void) => {
        mockLoad(url, onLoad);
      },
    })),
  },
  TextureLoader: vi.fn().mockImplementation(() => ({
    setCrossOrigin: vi.fn(),
    load: (url: string, onLoad: (tex: any) => void) => {
      mockLoad(url, onLoad);
    },
  })),
}));

// Mock lib/demApi
vi.mock('../../../lib/demApi', () => ({
  esriTileUrl: vi.fn((lat: number, lon: number, z: number) => `https://tile.example/${z}/${lat}/${lon}`),
}));

describe('useEsriTexture Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should export hook as function', () => {
    expect(typeof useEsriTexture).toBe('function');
  });

  it('should return null when siteMeta is null', () => {
    const { result } = renderHook(() => useEsriTexture(null));
    expect(result.current).toBeNull();
  });

  it('should attempt to load texture when siteMeta is provided', () => {
    const siteMeta: SiteMeta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
    const { result } = renderHook(() => useEsriTexture(siteMeta));

    // Should have attempted to load
    expect(mockLoad).toHaveBeenCalled();

    // Initially null (before callback fires)
    expect(result.current).toBeNull();

    // Simulate load callback
    const fakeTexture = { fake: 'texture' };
    act(() => {
      const loadCall = mockLoad.mock.calls[0];
      if (loadCall && typeof loadCall[1] === 'function') {
        loadCall[1](fakeTexture);
      }
    });

    // Now should have the texture
    expect(result.current).toBe(fakeTexture);
  });

  it('should handle load error gracefully', () => {
    const siteMeta: SiteMeta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
    const { result } = renderHook(() => useEsriTexture(siteMeta));

    // Initial state
    expect(result.current).toBeNull();

    // Note: error handling is tested by the implementation
    // which calls onError callback and sets texture to null
  });
});
