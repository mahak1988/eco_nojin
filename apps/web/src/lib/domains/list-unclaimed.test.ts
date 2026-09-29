import { readdirSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { getCatalogEntry, OUT_OF_CATALOGUE_ROUTES } from './page-catalog';

const APP = path.join(import.meta.dirname, '..', '..', 'app', '[locale]');

function walk(dir: string, acc: string[] = []): string[] {
  for (const item of readdirSync(dir, { withFileTypes: true })) {
    if (item.name.startsWith('_')) continue;
    const full = path.join(dir, item.name);
    if (item.isDirectory()) walk(full, acc);
    else if (item.name === 'page.tsx') acc.push(full);
  }
  return acc;
}

describe('diagnostic', () => {
  it('lists routes on disk that no catalogue entry claims', () => {
    const declared = new Set(OUT_OF_CATALOGUE_ROUTES.map((entry) => entry.path));
    const unclaimed = walk(APP)
      .map((file) => {
        const normalised = file.replace(/\\/g, '/');
        const at = normalised.indexOf('apps/web/src/app/[locale]');
        const rel = normalised.slice(at + 'apps/web/src/app/[locale]'.length);
        return rel.replace('/page.tsx', '') || '/';
      })
      .filter((route) => !declared.has(route) && getCatalogEntry(route) === undefined)
      .sort();
    console.log(`unclaimed: ${unclaimed.length}`);
    for (const route of unclaimed) console.log(`  ${route}`);
    expect(true).toBe(true);
  });
});
