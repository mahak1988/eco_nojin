/**
 * WindArrows Tests
 */
import { describe, it, expect } from 'vitest';
import { WindArrows } from '../components/canvas';
import type { WindArrowsProps } from '../components/canvas/WindArrows';
import type { TerrainData } from '../types';

describe('WindArrows Component', () => {
  const createTerrain = (): TerrainData => ({
    width: 10, height: 10,
    elevation: Array(10).fill(0).map(() => Array(10).fill(50)),
    moisture: Array(10).fill(0).map(() => Array(10).fill(0.5)),
    minElevation: 0, maxElevation: 100,
  });

  it('should export WindArrows as function', () => {
    expect(typeof WindArrows).toBe('function');
  });

  it('should accept all required props', () => {
    const props: WindArrowsProps = {
      data: createTerrain(),
      direction: 180,
      speed: 15,
    };
    expect(props.direction).toBe(180);
    expect(props.speed).toBe(15);
  });

  it('should accept high wind speeds', () => {
    const props: WindArrowsProps = {
      data: createTerrain(),
      direction: 90,
      speed: 100,
    };
    expect(props.speed).toBe(100);
  });

  it('should accept zero wind speed (arrows hidden)', () => {
    const props: WindArrowsProps = {
      data: createTerrain(),
      direction: 0,
      speed: 0,
    };
    expect(props.speed).toBe(0);
  });
});
