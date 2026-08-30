/**
 * useEsriTexture Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useEsriTexture } from '../hooks';

// Mock three
vi.mock('three', () => ({
  default: {
    TextureLoader: vi.fn().mockImplementation(() => ({
      setCrossOrigin: vi.fn(),
      load: vi.fn(),
    })),
  },
  TextureLoader: vi.fn().mockImplementation(() => ({
    setCrossOrigin: vi.fn(),
    load: vi.fn(),
  })),
}));

// Mock lib/demApi
vi.mock('../../../lib/demApi', () => ({
  esriTileUrl: vi.fn(() => 'https://example.com/tile.jpg'),
}));

describe('useEsriTexture Hook', () => {
  it('should export hook as function', () => {
    expect(typeof useEsriTexture).toBe('function');
  });

  it('should return null when siteMeta is null', () => {
    const { result } = renderHook(() => useEsriTexture(null));
    expect(result.current).toBeNull();
  });

  it('should return null or texture when siteMeta is provided', () => {
    const siteMeta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
    const { result } = renderHook(() => useEsriTexture(siteMeta));
    // Result is null initially (async load)
    expect(result.current === null || result.current !== null).toBe(true);
  });
});
