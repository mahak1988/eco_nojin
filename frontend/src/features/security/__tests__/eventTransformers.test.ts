/**
 * Event Transformers Tests
 */
import { describe, it, expect } from 'vitest';
import {
  computeHourlyData,
  calculateSecurityScore,
  getUniqueFailedIPs,
  filterByType,
} from '../utils/eventTransformers';
import type { SecurityEvent } from '../types';

const mockEvents: SecurityEvent[] = [
  {
    id: '1',
    type: 'Successful Login',
    detail: 'admin login',
    ip_address: '1.2.3.4',
    created_at: new Date().toISOString(),
    severity: 'low',
  },
  {
    id: '2',
    type: 'Failed Login',
    detail: 'failed attempt',
    ip_address: '5.6.7.8',
    created_at: new Date().toISOString(),
    severity: 'high',
  },
  {
    id: '3',
    type: 'Failed Login',
    detail: 'failed again',
    ip_address: '5.6.7.8', // Same IP
    created_at: new Date().toISOString(),
    severity: 'high',
  },
];

describe('eventTransformers', () => {
  describe('filterByType', () => {
    it('should filter successful logins', () => {
      expect(filterByType(mockEvents, 'Successful Login')).toHaveLength(1);
    });

    it('should filter failed logins', () => {
      expect(filterByType(mockEvents, 'Failed Login')).toHaveLength(2);
    });
  });

  describe('calculateSecurityScore', () => {
    it('should return 100 with no failures', () => {
      expect(calculateSecurityScore(0)).toBe(100);
    });

    it('should decrease with failures', () => {
      expect(calculateSecurityScore(5)).toBe(75);
    });

    it('should not go below 0', () => {
      expect(calculateSecurityScore(100)).toBe(0);
    });
  });

  describe('getUniqueFailedIPs', () => {
    it('should count unique IPs', () => {
      expect(getUniqueFailedIPs(mockEvents)).toBe(1); // Only 5.6.7.8
    });
  });

  describe('computeHourlyData', () => {
    it('should return 24 hours', () => {
      const result = computeHourlyData(mockEvents);
      expect(result).toHaveLength(24);
    });

    it('should have correct structure', () => {
      const result = computeHourlyData(mockEvents);
      expect(result[0]).toHaveProperty('hour');
      expect(result[0]).toHaveProperty('success');
      expect(result[0]).toHaveProperty('failed');
    });
  });
});
