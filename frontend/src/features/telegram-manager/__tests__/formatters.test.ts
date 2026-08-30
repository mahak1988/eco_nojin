/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { formatNumber, formatDateTime, formatTime } from '../utils/formatters';

describe('formatters', () => {
  describe('formatNumber', () => {
    it('should format large numbers', () => {
      const result = formatNumber(1234567);
      expect(result).toContain('1,234,567');
    });

    it('should handle zero', () => {
      expect(formatNumber(0)).toBe('0');
    });
  });

  describe('formatDateTime', () => {
    it('should format valid date string', () => {
      const result = formatDateTime('2026-01-15T10:30:00Z');
      expect(result).toBeTruthy();
      expect(result.length).toBeGreaterThan(0);
    });

    it('should handle invalid date gracefully', () => {
      const result = formatDateTime('invalid');
      expect(result).toBe('invalid');
    });
  });

  describe('formatTime', () => {
    it('should format time from Date object', () => {
      const date = new Date('2026-01-15T10:30:45');
      const result = formatTime(date);
      expect(result).toBeTruthy();
    });
  });
});
