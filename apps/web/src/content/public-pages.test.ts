import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const messagesDir = path.join(process.cwd(), 'messages');
const read = (locale: string) =>
  JSON.parse(readFileSync(path.join(messagesDir, `${locale}.json`), 'utf8')) as Record<
    string,
    Record<string, unknown>
  >;

const fa = read('fa');
const en = read('en');

/** Sections that must follow the T02 five-part contract (master plan §۶.۱). */
const FIVE_PART_SECTIONS = [
  'about',
  'services',
  'evidence',
  'ai',
  'trust',
  'developers',
  'accessibility',
] as const;

describe('Phase 1 public pages — T02 five-part content contract', () => {
  for (const section of FIVE_PART_SECTIONS) {
    it(`${section}: has title, lead, what, audience, limits, next in fa & en`, () => {
      for (const catalogue of [fa, en]) {
        const page = catalogue[section];
        expect(page, `${section} missing`).toBeTruthy();
        expect(page.title).toBeTruthy();
        expect(page.lead).toBeTruthy();
        expect(page.what).toBeTruthy();
        expect(page.audience).toBeTruthy();
        expect(Array.isArray(page.limits), `${section}.limits must be an array`).toBe(true);
        expect(Array.isArray(page.next), `${section}.next must be an array`).toBe(true);
        expect((page.limits as unknown[]).length).toBeGreaterThan(0);
        expect((page.next as unknown[]).length).toBeGreaterThan(0);
      }
    });
  }

  it('document pages are versioned and dated (T09)', () => {
    expect(fa.statements.versionLabel).toBeTruthy();
    expect(en.statements.versionLabel).toBeTruthy();
    expect(fa.legal.version).toBeTruthy();
    expect(en.legal.version).toBeTruthy();
  });

  it('learning library states its emptiness honestly', () => {
    expect(fa.learn.emptyTitle).toBeTruthy();
    expect(en.learn.emptyDesc).toBeTruthy();
  });
});
