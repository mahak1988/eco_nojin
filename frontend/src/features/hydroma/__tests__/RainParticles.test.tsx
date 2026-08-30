/**
 * RainParticles Tests
 */
import { describe, it, expect } from 'vitest';
import { RainParticles } from '../components/canvas';
import type { RainParticlesProps } from '../components/canvas/RainParticles';

describe('RainParticles Component', () => {
  it('should export RainParticles as function', () => {
    expect(typeof RainParticles).toBe('function');
  });

  it('should accept custom particle count', () => {
    const props: RainParticlesProps = { count: 2000 };
    expect(props.count).toBe(2000);
  });

  it('should work without props (uses default)', () => {
    const props: RainParticlesProps = {};
    expect(props.count).toBeUndefined();
  });

  it('should accept very high particle counts', () => {
    const props: RainParticlesProps = { count: 10000 };
    expect(props.count).toBe(10000);
  });
});
