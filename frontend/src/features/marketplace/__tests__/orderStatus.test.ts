/**
 * Order Status Tests
 */
import { describe, it, expect } from 'vitest';
import { isPendingOrder, isCompletedOrder, normalizeOrderStatus } from '../constants/orderStatus';

describe('orderStatus', () => {
  describe('isPendingOrder', () => {
    it('should return true for pending', () => {
      expect(isPendingOrder('pending')).toBe(true);
    });

    it('should return false for other statuses', () => {
      expect(isPendingOrder('confirmed')).toBe(false);
      expect(isPendingOrder('unknown')).toBe(false);
    });
  });

  describe('isCompletedOrder', () => {
    it('should return true for confirmed', () => {
      expect(isCompletedOrder('confirmed')).toBe(true);
    });

    it('should return true for completed', () => {
      expect(isCompletedOrder('completed')).toBe(true);
    });

    it('should return false for pending', () => {
      expect(isCompletedOrder('pending')).toBe(false);
    });
  });

  describe('normalizeOrderStatus', () => {
    it('should lowercase and normalize', () => {
      expect(normalizeOrderStatus('PENDING')).toBe('pending');
      expect(normalizeOrderStatus('Confirmed')).toBe('confirmed');
    });

    it('should return unknown for invalid', () => {
      expect(normalizeOrderStatus('invalid')).toBe('unknown');
      expect(normalizeOrderStatus(undefined)).toBe('unknown');
    });
  });
});
