import { describe, expect, it } from 'vitest';
import {
  CURRENT_PAGE_FILES_OBSERVED,
  getRouteManifestEntry,
  isRouteContext,
  PLANNING_CEILING,
  plannedPageTotal,
  routeManifest,
} from './route-manifest';

describe('route manifest foundation', () => {
  it('keeps the planning ceiling and current baseline explicit', () => {
    expect(PLANNING_CEILING).toBe(987);
    expect(CURRENT_PAGE_FILES_OBSERVED).toBe(175);
    expect(plannedPageTotal).toBe(PLANNING_CEILING);
  });

  it('has one unique entry for every planned context', () => {
    const ids = new Set(routeManifest.map((entry) => entry.id));
    const patterns = new Set(routeManifest.map((entry) => entry.pattern));

    expect(ids.size).toBe(routeManifest.length);
    expect(patterns.size).toBe(routeManifest.length);
    expect(routeManifest.every((entry) => entry.owner && entry.api && entry.tests.length > 0)).toBe(
      true,
    );
  });

  it('exposes context lookup and validation helpers', () => {
    expect(getRouteManifestEntry('marketplace')?.plannedPages).toBe(444);
    expect(getRouteManifestEntry('does-not-exist')).toBeUndefined();
    expect(isRouteContext('hydroma')).toBe(true);
    expect(isRouteContext('unknown')).toBe(false);
  });
});
