/**
 * useLiveFeedEvents Hook
 * =======================
 * Manages live feed events with proper interval cleanup.
 *
 * KEY FIX: Uses ref-based pattern to avoid stale closure.
 *
 * The problem with the old code:
 * - addEvent was not in useEffect dependencies
 * - setInterval captured old addEvent with old maxItems
 * - When maxItems changed, interval still used old closure
 *
 * The solution:
 * - Store latest addEvent in ref
 * - Interval callback reads from ref (always current)
 * - Dependencies simplified to [isPaused, pollInterval]
 *
 * @module features/live-feed/hooks
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { FeedEvent } from '../types';
import { generateEvent } from '../utils/eventGenerator';
import {
  DEFAULT_MAX_ITEMS,
  DEFAULT_POLL_INTERVAL_MS,
} from '../constants/eventTemplates';

interface UseLiveFeedEventsOptions {
  maxItems?: number;
  pollInterval?: number;
  autoStart?: boolean;
}

interface UseLiveFeedEventsReturn {
  events: FeedEvent[];
  isPaused: boolean;
  togglePause: () => void;
  addEvent: () => void;
  clearEvents: () => void;
}

export function useLiveFeedEvents(
  options: UseLiveFeedEventsOptions = {}
): UseLiveFeedEventsReturn {
  const {
    maxItems = DEFAULT_MAX_ITEMS,
    pollInterval = DEFAULT_POLL_INTERVAL_MS,
    autoStart = true,
  } = options;

  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [isPaused, setIsPaused] = useState(!autoStart);

  // Refs for interval management (solves stale closure)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seedRef = useRef<number>(Date.now());
  const maxItemsRef = useRef(maxItems);

  // Keep maxItems ref updated
  maxItemsRef.current = maxItems;

  /**
   * Add a new event to the feed.
   *
   * Uses maxItemsRef to always get current value (no stale closure).
   */
  const addEvent = useCallback(() => {
    seedRef.current += 1;
    const newEvent = generateEvent(seedRef.current);

    setEvents((prev) => {
      const updated = [newEvent, ...prev];
      return updated.slice(0, maxItemsRef.current); // ← Always current!
    });
  }, []);

  /**
   * Toggle pause/resume.
   */
  const togglePause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  /**
   * Clear all events.
   */
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  /**
   * Interval setup and cleanup.
   *
   * KEY: Dependencies are only [isPaused, pollInterval].
   * addEvent is NOT in dependencies because we use refs.
   */
  useEffect(() => {
    if (isPaused) {
      // Clear interval when paused
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Add initial event
    addEvent();

    // Start interval
    intervalRef.current = setInterval(addEvent, pollInterval);

    // Cleanup on unmount or dependency change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPaused, pollInterval, addEvent]);

  return {
    events,
    isPaused,
    togglePause,
    addEvent,
    clearEvents,
  };
}
