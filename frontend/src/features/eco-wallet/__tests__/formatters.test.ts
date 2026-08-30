/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { safeString, formatNumber, safeNumber } from '../utils/formatters';

describe('formatters', () => {
  describe('safeString', () => {
    it('should handle null', () => {
      expect(safeString(null)).toBe('N/A');
    });

    it('should handle undefined', () => {
      expect(safeString(undefined)).toBe('N/A');
    });

    it('should pass through strings', () => {
      expect(safeString('hello')).toBe('hello');
    });

    it('should convert numbers', () => {
      expect(safeString(42)).toBe('42');
    });

    it('should convert booleans', () => {
      expect(safeString(true)).toBe('true');
    });

    it('should stringify objects', () => {
      expect(safeString({ a: 1 })).toBe('{"a":1}');
    });

    it('should use fallback', () => {
      expect(safeString(null, 'custom')).toBe('custom');
    });
  });

  describe('formatNumber', () => {
    it('should format numbers', () => {
      expect(formatNumber(1234567)).toBeTruthy();
    });

    it('should handle undefined', () => {
      expect(formatNumber(undefined)).toBe('0');
    });
  });

  describe('safeNumber', () => {
    it('should return number when valid', () => {
      expect(safeNumber(42)).toBe(42);
    });

    it('should return fallback for undefined', () => {
      expect(safeNumber(undefined, 10)).toBe(10);
    });

    it('should return fallback for NaN', () => {
      expect(safeNumber(NaN, 5)).toBe(5);
    });
  });
});
