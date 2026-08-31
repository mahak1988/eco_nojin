/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { formatUSD, formatCrypto, truncateAddress, truncateHash } from '../utils/formatters';

describe('formatters', () => {
  describe('formatUSD', () => {
    it('should format as USD currency', () => {
      expect(formatUSD(1234.56)).toContain('1,234.56');
    });

    it('should respect maxDigits', () => {
      expect(formatUSD(1234.5678, 2)).not.toContain('5678');
    });

    it('should handle zero', () => {
      expect(formatUSD(0)).toContain('0.00');
    });
  });

  describe('formatCrypto', () => {
    it('should format crypto amounts', () => {
      expect(formatCrypto(0.4523)).toContain('0.4523');
    });

    it('should handle large values', () => {
      expect(formatCrypto(15420.75)).toContain('15,420');
    });
  });

  describe('truncateAddress', () => {
    it('should truncate long addresses', () => {
      const address = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb';
      const result = truncateAddress(address);
      expect(result).toContain('...');
      expect(result.length).toBeLessThan(address.length);
    });

    it('should preserve short addresses', () => {
      const short = '0x123';
      expect(truncateAddress(short)).toBe(short);
    });
  });

  describe('truncateHash', () => {
    it('should truncate transaction hashes', () => {
      const hash = '0x' + 'a'.repeat(64);
      const result = truncateHash(hash);
      expect(result).toContain('...');
    });
  });
});
