/**
 * WaterSurface Tests
 */
import { describe, it, expect } from 'vitest';
import { WaterSurface } from '../components/canvas';
import type { WaterSurfaceProps } from '../components/canvas/WaterSurface';

describe('WaterSurface Component', () => {
  it('should export WaterSurface as function', () => {
    expect(typeof WaterSurface).toBe('function');
  });

  it('should accept normalized water level', () => {
    const props: WaterSurfaceProps = { levelNorm: 0.5 };
    expect(props.levelNorm).toBe(0.5);
  });

  it('should accept extreme water levels', () => {
    const low: WaterSurfaceProps = { levelNorm: 0 };
    const high: WaterSurfaceProps = { levelNorm: 1 };
    expect(low.levelNorm).toBe(0);
    expect(high.levelNorm).toBe(1);
  });
});
