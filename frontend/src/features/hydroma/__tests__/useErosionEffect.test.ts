/**
 * useErosionEffect Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useErosionEffect } from '../hooks';

describe('useErosionEffect Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock fetch globally
    global.fetch = vi.fn();
  });

  it('should export hook as function', () => {
    expect(typeof useErosionEffect).toBe('function');
  });

  it('should return initial state', () => {
    const { result } = renderHook(() => useErosionEffect());

    expect(result.current.effect).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('');
  });

  it('should expose fetchEffect function', () => {
    const { result } = renderHook(() => useErosionEffect());
    expect(typeof result.current.fetchEffect).toBe('function');
  });

  it('should expose clear function', () => {
    const { result } = renderHook(() => useErosionEffect());
    expect(typeof result.current.clear).toBe('function');
  });

  it('should handle successful fetch', async () => {
    const mockEffect = {
      op_type: 'gabion',
      op_fa: 'دیوار گابیونی',
      A_before_t_ha_yr: 10,
      A_after_t_ha_yr: 5,
      reduction_pct: 50,
      note_fa: 'تست',
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEffect,
    });

    const { result } = renderHook(() => useErosionEffect());

    await act(async () => {
      await result.current.fetchEffect('SITE265', 'gabion');
    });

    expect(result.current.effect).toEqual(mockEffect);
    expect(result.current.error).toBe('');
    expect(result.current.loading).toBe(false);
  });

  it('should handle fetch error', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    const { result } = renderHook(() => useErosionEffect());

    await act(async () => {
      await result.current.fetchEffect('INVALID', 'gabion');
    });

    expect(result.current.effect).toBeNull();
    expect(result.current.error).toContain('404');
    expect(result.current.loading).toBe(false);
  });

  it('should clear effect', async () => {
    const mockEffect = {
      op_type: 'gabion',
      op_fa: 'دیوار گابیونی',
      A_before_t_ha_yr: 10,
      A_after_t_ha_yr: 5,
      reduction_pct: 50,
      note_fa: 'تست',
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockEffect,
    });

    const { result } = renderHook(() => useErosionEffect());

    await act(async () => {
      await result.current.fetchEffect('SITE265', 'gabion');
    });

    expect(result.current.effect).not.toBeNull();

    act(() => {
      result.current.clear();
    });

    expect(result.current.effect).toBeNull();
    expect(result.current.error).toBe('');
  });
});
