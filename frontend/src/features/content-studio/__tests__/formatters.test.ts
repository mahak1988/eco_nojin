/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { truncateId, formatDate, normalizeStatus, getStatusBadgeClass } from '../utils/formatters';

describe('formatters', () => {
  describe('truncateId', () => {
    it('should truncate long IDs', () => {
      expect(truncateId('1234567890abcdef')).toBe('12345678');
    });

    it('should preserve short IDs', () => {
      expect(truncateId('123')).toBe('123');
    });

    it('should use fallback for undefined', () => {
      expect(truncateId(undefined)).toBe('N/A');
    });
  });

  describe('formatDate', () => {
    it('should format valid date', () => {
      const result = formatDate('2026-01-15T10:30:00Z');
      expect(result).toBeTruthy();
      expect(result).not.toBe('-');
    });

    it('should use fallback for undefined', () => {
      expect(formatDate(undefined)).toBe('-');
    });
  });

  describe('normalizeStatus', () => {
    it('should lowercase status', () => {
      expect(normalizeStatus('PUBLISHED')).toBe('published');
      expect(normalizeStatus('Draft')).toBe('draft');
    });

    it('should handle undefined', () => {
      expect(normalizeStatus(undefined)).toBe('');
    });
  });

  describe('getStatusBadgeClass', () => {
    it('should return success for published', () => {
      expect(getStatusBadgeClass('published')).toBe('success');
    });

    it('should return warning for draft', () => {
      expect(getStatusBadgeClass('draft')).toBe('warning');
    });

    it('should return info for other', () => {
      expect(getStatusBadgeClass('scheduled')).toBe('info');
    });
  });
});
