import { describe, expect, it } from 'vitest';
import { cn } from '../src/cn';
import { convertArea } from '../src/units';

describe('utils/cn', () => {
  it('merges tailwind classes with conflict resolution', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
    expect(cn('text-red-500', false && 'text-blue-500')).toBe('text-red-500');
  });
});

describe('utils/units', () => {
  it('converts area between ha, m², km² and acre', () => {
    expect(convertArea(1, 'ha', 'm2')).toBeCloseTo(10_000, 6);
    expect(convertArea(1, 'km2', 'ha')).toBe(100);
    expect(convertArea(1, 'acre', 'ha')).toBeCloseTo(0.40468564224, 9);
  });
});