import { readdirSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  CURRENT_PAGE_FILES_OBSERVED,
  getRouteManifestEntry,
  isRouteContext,
  PLANNING_CEILING,
  plannedPageTotal,
  routeManifest,
} from './route-manifest';

const APP_ROOT = path.resolve(import.meta.dirname, '..', 'app');

/** Count `page.tsx` on disk rather than trusting a number typed into a file. */
function countPageFiles(dir: string, acc: number = 0): number {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) acc = countPageFiles(full, acc);
    else if (entry.name === 'page.tsx') acc += 1;
  }
  return acc;
}

describe('route manifest foundation', () => {
  it('keeps the planning ceiling and current baseline explicit', () => {
    expect(PLANNING_CEILING).toBe(987);
    expect(CURRENT_PAGE_FILES_OBSERVED).toBe(352);
    expect(plannedPageTotal).toBe(PLANNING_CEILING);
  });

  it('matches the baseline against the filesystem, so it cannot drift again', () => {
    // The constant sat at 175 while the real count was 241 because nothing
    // compared it to disk. `page-catalog.test.ts` scans the same tree for
    // routable pages; this assertion is the cheap cross-check for the whole tree.
    expect(CURRENT_PAGE_FILES_OBSERVED).toBe(countPageFiles(APP_ROOT));
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
