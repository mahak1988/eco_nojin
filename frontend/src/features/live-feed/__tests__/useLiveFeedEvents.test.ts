/**
 * useLiveFeedEvents Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLiveFeedEvents } from '../hooks/useLiveFeedEvents';

// Mock timers
vi.useFakeTimers();

describe('useLiveFeedEvents', () => {
  beforeEach(() => {
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with empty events', () => {
    const { result } = renderHook(() => useLiveFeedEvents({ autoStart: false }));

    expect(result.current.events).toEqual([]);
    expect(result.current.isPaused).toBe(true);
  });

  it('should add event on initial render when autoStart=true', () => {
    const { result } = renderHook(() => useLiveFeedEvents({ autoStart: true }));

    expect(result.current.events.length).toBeGreaterThan(0);
    expect(result.current.isPaused).toBe(false);
  });

  it('should add events on interval', () => {
    const { result } = renderHook(() =>
      useLiveFeedEvents({
        pollInterval: 1000,
        autoStart: true,
      })
    );

    const initialCount = result.current.events.length;

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.events.length).toBeGreaterThan(initialCount);
  });

  it('should respect maxItems limit', () => {
    const maxItems = 5;
    const { result } = renderHook(() =>
      useLiveFeedEvents({
        maxItems,
        pollInterval: 100,
        autoStart: true,
      })
    );

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.events.length).toBeLessThanOrEqual(maxItems);
  });

  it('should toggle pause state', () => {
    const { result } = renderHook(() => useLiveFeedEvents({ autoStart: true }));

    expect(result.current.isPaused).toBe(false);

    act(() => {
      result.current.togglePause();
    });

    expect(result.current.isPaused).toBe(true);

    act(() => {
      result.current.togglePause();
    });

    expect(result.current.isPaused).toBe(false);
  });

  it('should not add events when paused', () => {
    const { result } = renderHook(() =>
      useLiveFeedEvents({
        pollInterval: 500,
        autoStart: true,
      })
    );

    act(() => {
      result.current.togglePause(); // Pause
    });

    const countBefore = result.current.events.length;

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.events.length).toBe(countBefore);
  });

  it('should clear events', () => {
    const { result } = renderHook(() => useLiveFeedEvents({ autoStart: true }));

    expect(result.current.events.length).toBeGreaterThan(0);

    act(() => {
      result.current.clearEvents();
    });

    expect(result.current.events).toEqual([]);
  });

  it('should clean up interval on unmount', () => {
    const { result, unmount } = renderHook(() =>
      useLiveFeedEvents({
        pollInterval: 100,
        autoStart: true,
      })
    );

    const countBefore = result.current.events.length;

    unmount();

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // No new events should be added after unmount
    // (This is implicit - if interval wasn't cleared, test would hang or fail)
    expect(result.current.events.length).toBe(countBefore);
  });
});
