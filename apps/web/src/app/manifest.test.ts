import { describe, expect, it } from 'vitest';
import manifest from './manifest';

describe('PWA manifest', () => {
  it('declares a standalone offline-capable application', () => {
    const value = manifest();

    expect(value.display).toBe('standalone');
    expect(value.start_url).toBe('/fa');
    expect(value.icons).toBeDefined();
    expect(value.icons?.length).toBeGreaterThan(0);
  });
});
