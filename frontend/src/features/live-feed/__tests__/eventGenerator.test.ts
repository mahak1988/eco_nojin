/**
 * Event Generator Tests (Final)
 */
import { describe, it, expect } from 'vitest';
import { generateEvent, generateMultipleEvents } from '../utils/eventGenerator';

describe('eventGenerator', () => {
  describe('generateEvent', () => {
    it('should generate valid event', () => {
      const event = generateEvent(12345);
      expect(event).toBeDefined();
      expect(event.id).toBeDefined();
      expect(event.type).toBeDefined();
      expect(event.timestamp).toBeInstanceOf(Date);
    });

    it('should be deterministic', () => {
      const e1 = generateEvent(99999);
      const e2 = generateEvent(99999);
      expect(e1.type).toBe(e2.type);
      expect(e1.title).toBe(e2.title);
    });

    it('should use custom templates', () => {
      const custom = [{ type: 'success' as const, title: 'Test', message: 'Msg', icon: '✓' }];
      const event = generateEvent(42, custom);
      expect(event.title).toBe('Test');
    });
  });

  describe('generateMultipleEvents', () => {
    it('should generate correct count', () => {
      const events = generateMultipleEvents(5);
      expect(events.length).toBe(5);
    });
  });
});
