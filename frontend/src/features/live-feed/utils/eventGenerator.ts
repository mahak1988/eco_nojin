/**
 * Event Generator
 * =================
 * Deterministic event generation with seed-based random.
 *
 * Replaces Math.random() with reproducible pseudo-random number generator.
 *
 * @module features/live-feed/utils
 */

import type { FeedEvent, EventTemplate } from '../types';
import { EVENT_TEMPLATES } from '../constants/eventTemplates';

/**
 * Simple seeded random number generator (LCG).
 *
 * @see https://en.wikipedia.org/wiki/Linear_congruential_generator
 */
function seededRandom(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 2 ** 32;
    return state / 2 ** 32;
  };
}

/**
 * Generate unique event ID.
 *
 * Uses timestamp + seed-based random for uniqueness.
 * Replaces deprecated substr() with slice().
 */
function generateEventId(seed: number): string {
  const timestamp = Date.now();
  const random = seededRandom(seed);
  const randomPart = Math.floor(random() * 2 ** 32).toString(36);
  return `evt-${timestamp}-${randomPart.slice(0, 9)}`;
}

/**
 * Generate a new feed event.
 *
 * @param seed - Random seed (defaults to Date.now() for variety)
 * @param templates - Event templates to choose from
 */
export function generateEvent(
  seed: number = Date.now(),
  templates: EventTemplate[] = EVENT_TEMPLATES
): FeedEvent {
  const random = seededRandom(seed);
  const templateIndex = Math.floor(random() * templates.length);
  const template = templates[templateIndex];

  return {
    id: generateEventId(seed),
    type: template.type,
    title: template.title,
    message: template.message,
    timestamp: new Date(),
  };
}

/**
 * Generate multiple events for testing/initialization.
 */
export function generateMultipleEvents(
  count: number,
  startSeed: number = 42
): FeedEvent[] {
  return Array.from({ length: count }, (_, i) =>
    generateEvent(startSeed + i)
  );
}
