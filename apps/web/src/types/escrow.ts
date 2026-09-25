export const ESCROW_STATES = ['created', 'locked', 'released', 'reversed', 'completed'] as const;
export type EscrowState = (typeof ESCROW_STATES)[number];
export type EscrowAction = 'lock' | 'release' | 'reverse' | 'complete';

export const ESCROW_TRANSITIONS: Record<EscrowState, readonly EscrowState[]> = {
  created: ['locked'],
  locked: ['released', 'reversed'],
  released: ['completed'],
  reversed: ['completed'],
  completed: [],
};

export interface EscrowSnapshot {
  id: string;
  orderId: string;
  state: EscrowState;
  amount: number;
  currency: string;
  updatedAt: string;
}

export function canTransition(state: EscrowState, nextState: EscrowState): boolean {
  return ESCROW_TRANSITIONS[state].includes(nextState);
}

export function availableActions(state: EscrowState): EscrowAction[] {
  const actions: Record<EscrowState, EscrowAction[]> = {
    created: ['lock'],
    locked: ['release', 'reverse'],
    released: ['complete'],
    reversed: ['complete'],
    completed: [],
  };
  return actions[state];
}

export function transitionEscrow(
  snapshot: EscrowSnapshot,
  nextState: EscrowState,
  updatedAt = new Date().toISOString(),
): EscrowSnapshot {
  if (!canTransition(snapshot.state, nextState)) {
    throw new Error(`Invalid escrow transition: ${snapshot.state} -> ${nextState}`);
  }
  return { ...snapshot, state: nextState, updatedAt };
}
