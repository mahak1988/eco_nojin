/**
 * Security Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { getScoreColor, formatEventTime, formatSuccessRate } from '../utils/formatters';

describe('formatters', () => {
  describe('getScoreColor', () => {
    it('should return primary for > 80', () => {
      expect(getScoreColor(90)).toContain('primary');
    });

    it('should return secondary for > 50', () => {
      expect(getScoreColor(60)).toContain('secondary');
    });

    it('should return danger for <= 50', () => {
      expect(getScoreColor(40)).toContain('danger');
    });
  });

  describe('formatEventTime', () => {
    it('should format valid date', () => {
      const result = formatEventTime(new Date().toISOString());
      expect(result).not.toBe('-');
    });

    it('should return - for invalid', () => {
      expect(formatEventTime('')).toBe('-');
      expect(formatEventTime('invalid')).toBe('-');
    });
  });

  describe('formatSuccessRate', () => {
    it('should calculate percentage', () => {
      expect(formatSuccessRate(3, 4)).toBe('75.0');
    });

    it('should handle zero total', () => {
      expect(formatSuccessRate(0, 0)).toBe('0');
    });
  });
});
