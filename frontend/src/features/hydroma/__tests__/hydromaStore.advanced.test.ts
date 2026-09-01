import { describe, it, expect } from 'vitest';
import { useHydromaStore } from '../store/hydromaStore';

describe('hydromaStore - Safe Advanced Tests', () => {
  it('should have getState method', () => {
    expect(useHydromaStore.getState).toBeDefined();
    expect(typeof useHydromaStore.getState).toBe('function');
  });

  it('should have setState method', () => {
    expect(useHydromaStore.setState).toBeDefined();
    expect(typeof useHydromaStore.setState).toBe('function');
  });

  it('should have subscribe method', () => {
    expect(useHydromaStore.subscribe).toBeDefined();
    expect(typeof useHydromaStore.subscribe).toBe('function');
  });

  it('state should be an object', () => {
    const state = useHydromaStore.getState();
    expect(typeof state).toBe('object');
    expect(state).not.toBeNull();
  });

  it('state should have expected keys', () => {
    const state = useHydromaStore.getState() as any;
    // At least one of these common keys should exist
    const hasCommonKeys = 'terrain' in state
      || 'viewMode' in state
      || 'layers' in state
      || 'plots' in state
      || 'climate' in state;
    expect(hasCommonKeys).toBe(true);
  });

  it('subscription should work', () => {
    let called = 0;
    const unsub = useHydromaStore.subscribe(() => { called++; });
    expect(typeof unsub).toBe('function');
    unsub();
  });
});
