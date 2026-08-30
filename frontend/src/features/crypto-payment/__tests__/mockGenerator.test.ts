/**
 * Mock Generator Tests
 */
import { describe, it, expect } from 'vitest';
import { generateMockTransaction } from '../utils/mock_generator';

describe('generateMockTransaction', () => {
  it('should generate valid transaction structure', () => {
    const tx = generateMockTransaction('tx-1', 12345);

    expect(tx.id).toBe('tx-1');
    expect(['btc', 'usdt', 'eth']).toContain(tx.type);
    expect(['confirmed', 'pending', 'failed']).toContain(tx.status);
    expect(typeof tx.amount).toBe('number');
    expect(typeof tx.usdValue).toBe('number');
    expect(tx.txHash).toMatch(/^0x[0-9a-f]{64}$/);
    expect(tx.from).toMatch(/^0x[0-9a-f]{40}$/);
  });

  it('should be deterministic with same seed', () => {
    const tx1 = generateMockTransaction('tx-1', 99999);
    const tx2 = generateMockTransaction('tx-2', 99999);

    // Same seed → same values (except id and timestamp)
    expect(tx1.type).toBe(tx2.type);
    expect(tx1.amount).toBe(tx2.amount);
    expect(tx1.status).toBe(tx2.status);
    expect(tx1.txHash).toBe(tx2.txHash);
  });

  it('should produce different results with different seeds', () => {
    const tx1 = generateMockTransaction('tx-1', 1);
    const tx2 = generateMockTransaction('tx-2', 2);

    // Different seeds → at least one difference
    const different =
      tx1.type !== tx2.type ||
      tx1.amount !== tx2.amount ||
      tx1.status !== tx2.status;
    expect(different).toBe(true);
  });
});
