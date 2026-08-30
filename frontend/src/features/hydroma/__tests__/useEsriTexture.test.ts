/**
 * useEsriTexture Tests
 * =====================
 * Uses vi.hoisted() to define mocks before vi.mock() runs.
 * This is Vitest's officially recommended approach.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useEsriTexture } from '../hooks';
import type { SiteMeta } from '../types';

// ─────────────────────────────────────────────────────────────────────
// vi.hoisted() runs BEFORE vi.mock() factory executes
// This solves the "Cannot access before initialization" error
// ─────────────────────────────────────────────────────────────────────
const mocks = vi.hoisted(() => {
  const loadCalls: Array<{
    url: string;
    onLoad: (tex: any) => void;
    onProgress?: () => void;
    onError?: (err: any) => void;
  }> = [];

  class MockTextureLoader {
    setCrossOrigin = vi.fn();
    load(
      url: string,
      onLoad: (tex: any) => void,
      onProgress?: () => void,
      onError?: (err: any) => void
    ) {
      loadCalls.push({ url, onLoad, onProgress, onError });
    }
  }

  return { loadCalls, MockTextureLoader };
});

// ─────────────────────────────────────────────────────────────────────
// vi.mock factory can now safely reference mocks.*
// ─────────────────────────────────────────────────────────────────────
vi.mock('three', () => {
  class Vector3 {
    constructor(public x = 0, public y = 0, public z = 0) {}
  }

  const THREE = {
    TextureLoader: mocks.MockTextureLoader,
    Vector3,
    PlaneGeometry: class {},
    BufferAttribute: class {},
    DoubleSide: 2,
    MOUSE: { ROTATE: 0, DOLLY: 1, PAN: 2 },
    TOUCH: { ROTATE: 0, DOLLY_PAN: 1 },
  };

  return {
    ...THREE,
    default: THREE,
  };
});

// Mock lib/demApi
vi.mock('../../../lib/demApi', () => ({
  esriTileUrl: vi.fn(
    (lat: number, lon: number, z: number) =>
      `https://tile.example/${z}/${lat}/${lon}`
  ),
}));

describe('useEsriTexture Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.loadCalls.length = 0;
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

    // Should have called loader.load
    expect(mocks.loadCalls.length).toBeGreaterThan(0);
    expect(mocks.loadCalls[0].url).toContain('35.7');

    // Initially null (before callback fires)
    expect(result.current).toBeNull();

    // Simulate successful load callback
    const fakeTexture = { dispose: vi.fn(), fake: 'texture' };
    act(() => {
      mocks.loadCalls[0].onLoad(fakeTexture);
    });

    // Now should have the texture
    expect(result.current).toBe(fakeTexture);
  });

  it('should handle load error gracefully', () => {
    const siteMeta: SiteMeta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
    const { result } = renderHook(() => useEsriTexture(siteMeta));

    expect(result.current).toBeNull();

    // Simulate error callback
    act(() => {
      if (mocks.loadCalls[0] && mocks.loadCalls[0].onError) {
        mocks.loadCalls[0].onError(new Error('Network error'));
      }
    });

    // Should remain null after error
    expect(result.current).toBeNull();
  });

  it('should cleanup texture on unmount', () => {
    const siteMeta: SiteMeta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
    const disposeMock = vi.fn();
    const { result, unmount } = renderHook(() => useEsriTexture(siteMeta));

    // Load texture
    const fakeTexture = { dispose: disposeMock, fake: 'texture' };
    act(() => {
      mocks.loadCalls[0].onLoad(fakeTexture);
    });

    expect(result.current).toBe(fakeTexture);

    // Unmount - should dispose
    unmount();

    expect(disposeMock).toHaveBeenCalled();
  });
});
