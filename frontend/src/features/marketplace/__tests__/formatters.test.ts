/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  getOrderAmount,
  truncateId,
  safeString,
} from '../utils/formatters';

describe('formatters', () => {
  describe('formatCurrency', () => {
    it('should format number with locale', () => {
      const result = formatCurrency(1234567);
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });

    it('should respect maxDigits', () => {
      const result = formatCurrency(1234.5678, 'en-US', 2);
      expect(result).toContain('1,234.57');
    });
  });

  describe('getOrderAmount', () => {
    it('should prefer total over amount', () => {
      expect(getOrderAmount({ total: 100, amount: 50 })).toBe(100);
    });

    it('should fallback to amount', () => {
      expect(getOrderAmount({ amount: 75 })).toBe(75);
    });

    it('should return 0 when both missing', () => {
      expect(getOrderAmount({})).toBe(0);
    });
  });

  describe('truncateId', () => {
    it('should truncate long IDs', () => {
      expect(truncateId('1234567890')).toBe('12345678');
    });

    it('should preserve short IDs', () => {
      expect(truncateId('123')).toBe('123');
    });

    it('should use fallback for undefined', () => {
      expect(truncateId(undefined)).toBe('N/A');
    });
  });

  describe('safeString', () => {
    it('should pass through strings', () => {
      expect(safeString('hello')).toBe('hello');
    });

    it('should handle null', () => {
      expect(safeString(null)).toBe('-');
    });

    it('should handle numbers', () => {
      expect(safeString(42)).toBe('42');
    });
  });
});
