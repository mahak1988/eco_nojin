import { describe, expect, it } from 'vitest';
import { availableActions, canTransition, type EscrowSnapshot, transitionEscrow } from './escrow';

const snapshot: EscrowSnapshot = {
  id: 'escrow-1',
  orderId: 'order-1',
  state: 'created',
  amount: 100,
  currency: 'IRT',
  updatedAt: '2026-09-24T00:00:00.000Z',
};

describe('escrow state machine', () => {
  it('matches the backend transition graph', () => {
    expect(canTransition('created', 'locked')).toBe(true);
    expect(canTransition('locked', 'released')).toBe(true);
    expect(canTransition('locked', 'reversed')).toBe(true);
    expect(canTransition('released', 'completed')).toBe(true);
    expect(canTransition('created', 'completed')).toBe(false);
    expect(canTransition('completed', 'released')).toBe(false);
  });

  it('transitions with a new observation time', () => {
    const next = transitionEscrow(snapshot, 'locked', '2026-09-24T01:00:00.000Z');
    expect(next.state).toBe('locked');
    expect(next.updatedAt).toBe('2026-09-24T01:00:00.000Z');
  });

  it('rejects invalid transitions and exposes allowed actions', () => {
    expect(() => transitionEscrow(snapshot, 'released')).toThrow('Invalid escrow transition');
    expect(availableActions('created')).toEqual(['lock']);
    expect(availableActions('locked')).toEqual(['release', 'reverse']);
    expect(availableActions('completed')).toEqual([]);
  });
});
