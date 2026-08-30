/**
 * Mock Data Tests
 */
import { describe, it, expect } from 'vitest';
import {
  generateTransactionHistory,
  DEFAULT_TRANSACTION_HISTORY,
} from '../constants/mockData';
import { CHART_CONFIG } from '../constants/config';

describe('mockData', () => {
  describe('generateTransactionHistory', () => {
    it('should generate correct number of days', () => {
      const history = generateTransactionHistory();
      expect(history).toHaveLength(CHART_CONFIG.days);
    });

    it('should be deterministic with same seed', () => {
      const h1 = generateTransactionHistory(CHART_CONFIG, 42);
      const h2 = generateTransactionHistory(CHART_CONFIG, 42);
      expect(h1).toEqual(h2);
    });

    it('should respect earnings range', () => {
      const history = generateTransactionHistory();
      for (const point of history) {
        expect(point.earnings).toBeGreaterThanOrEqual(CHART_CONFIG.earningsRange.min);
        expect(point.earnings).toBeLessThanOrEqual(CHART_CONFIG.earningsRange.max);
      }
    });

    it('should respect redemptions range', () => {
      const history = generateTransactionHistory();
      for (const point of history) {
        expect(point.redemptions).toBeGreaterThanOrEqual(CHART_CONFIG.redemptionsRange.min);
        expect(point.redemptions).toBeLessThanOrEqual(CHART_CONFIG.redemptionsRange.max);
      }
    });
  });

  describe('DEFAULT_TRANSACTION_HISTORY', () => {
    it('should be pre-generated', () => {
      expect(DEFAULT_TRANSACTION_HISTORY).toHaveLength(30);
    });
  });
});
