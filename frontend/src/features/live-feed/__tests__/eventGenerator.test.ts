/**
 * Event Generator Tests
 */
import { describe, it, expect } from 'vitest';
import { generateEvent, generateMultipleEvents } from '../utils/eventGenerator';
import { EVENT_TEMPLATES } from '../constants/eventTemplates';

describe('eventGenerator', () => {
  describe('generateEvent', () => {
    it('should generate valid event structure', () => {
      const event = generateEvent(12345);

      expect(event.id).toMatch(/^evt-/);
      expect(['success', 'warning', 'error', 'info']).toContain(event.type);
      expect(typeof event.title).toBe('string');
      expect(typeof event.message).toBe('string');
      expect(event.timestamp).toBeInstanceOf(Date);
    });

    it('should be deterministic with same seed', () => {
      const event1 = generateEvent(99999);
      const event2 = generateEvent(99999);

      // Same seed → same type, title, message (different id due to Date.now())
      expect(event1.type).toBe(event2.type);
      expect(event1.title).toBe(event2.title);
      expect(event1.message).toBe(event2.message);
    });

    it('should produce different results with different seeds', () => {
      const events = Array.from({ length: 10 }, (_, i) =>
        generateEvent(i * 1000)
      );

      // At least some should be different
      const types = new Set(events.map((e) => e.type));
      expect(types.size).toBeGreaterThan(1);
    });

    it('should use provided templates', () => {
      const customTemplates = [
        { type: 'success' as const, title: 'Custom', message: 'Test', icon: '✓' },
      ];

      const event = generateEvent(42, customTemplates);
      expect(event.title).toBe('Custom');
      expect(event.message).toBe('Test');
    });
  });

  describe('generateMultipleEvents', () => {
    it('should generate requested count', () => {
      const events = generateMultipleEvents(5);
      expect(events).toHaveLength(5);
    });

    it('should generate unique events', () => {
      const events = generateMultipleEvents(10, 1);

      // All should have different timestamps (at least)
      const timestamps = events.map((e) => e.timestamp.getTime());
      const uniqueTimestamps = new Set(timestamps);
      expect(uniqueTimestamps.size).toBe(events.length);
    });
  });
});
