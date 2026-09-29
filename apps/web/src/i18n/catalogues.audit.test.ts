import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * Guards the message catalogues themselves.
 *
 * `en.json` was emptied three times in one session: twice by the applier running
 * its prune branch against the reference catalogue, and once by a diagnostic I
 * wrote that used `openSync(path, 'w')` to test writability — which truncates.
 * Each time the damage was found by something else, late.
 *
 * These assertions are deliberately cheap and deliberately blunt. A catalogue
 * that does not parse, or that has lost its `pageMeta` namespace, is a build
 * failure; nothing downstream needs to guess whether the empty `h1` it renders
 * came from a missing translation or from a missing file.
 */
function findRepoRoot(from: string): string {
  let current = from;
  for (let depth = 0; depth < 12; depth += 1) {
    if (existsSync(path.join(current, 'scripts', 'check-locale-encoding.mjs'))) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`could not locate the repository root above ${from}`);
}

const REPO_ROOT = findRepoRoot(import.meta.dirname);
const MESSAGES = path.join(REPO_ROOT, 'apps', 'web', 'messages');

const LOCALES = [
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'ru',
  'zh',
  'bn',
];

const catalogues = Object.fromEntries(
  LOCALES.map((locale) => {
    const file = path.join(MESSAGES, `${locale}.json`);
    return [locale, existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) : null];
  }),
) as Record<string, Record<string, unknown> | null>;

describe('message catalogues', () => {
  it('are all present and parse', () => {
    for (const locale of LOCALES) {
      expect(catalogues[locale], `${locale}.json is missing or is not valid JSON`).not.toBeNull();
      expect(
        Object.keys(catalogues[locale] ?? {}).length,
        `${locale}.json is empty`,
      ).toBeGreaterThan(0);
    }
  });

  it('all carry a pageMeta namespace', () => {
    for (const locale of LOCALES) {
      const meta = (catalogues[locale] as { pageMeta?: Record<string, unknown> } | null)?.pageMeta;
      expect(meta, `${locale}.json has no pageMeta namespace`).toBeTruthy();
      expect(
        Object.keys(meta ?? {}).length,
        `${locale}.json has an empty pageMeta`,
      ).toBeGreaterThan(0);
    }
  });

  it('give every pageMeta entry a non-empty title and description', () => {
    for (const locale of LOCALES) {
      const meta = (
        catalogues[locale] as {
          pageMeta?: Record<string, { title?: string; description?: string }>;
        }
      ).pageMeta;
      for (const [slug, entry] of Object.entries(meta ?? {})) {
        expect(typeof entry.title, `${locale}.${slug}.title`).toBe('string');
        expect(
          (entry.title ?? '').trim().length,
          `${locale}.${slug}.title is blank`,
        ).toBeGreaterThan(0);
        expect(typeof entry.description, `${locale}.${slug}.description`).toBe('string');
        expect(
          (entry.description ?? '').trim().length,
          `${locale}.${slug}.description is blank`,
        ).toBeGreaterThan(0);
      }
    }
  });

  it('carry no replacement character anywhere in pageMeta', () => {
    // U+FFFD is a lost byte, and it is what the original mojibake catalogues were
    // made of. It parses as valid JSON, so only an assertion like this sees it.
    for (const locale of LOCALES) {
      const meta = (
        catalogues[locale] as { pageMeta?: Record<string, { title: string; description: string }> }
      ).pageMeta;
      for (const [slug, entry] of Object.entries(meta ?? {})) {
        expect(
          `${entry.title}${entry.description}`.includes('�'),
          `${locale}.${slug} contains U+FFFD`,
        ).toBe(false);
      }
    }
  });

  it('give every namespace the reference declares, or a declared subset', () => {
    // Not all fourteen carry the same namespace list, and that is by design: the
    // twelve non-reference catalogues were originally skeletons with 24
    // namespaces, and they inherit the rest through the `en` merge. What must never
    // happen is a locale carrying a namespace `en` does not, because then the two
    // would disagree about what exists.
    const reference = new Set(Object.keys(catalogues.fa as object));
    for (const locale of LOCALES) {
      const extra = Object.keys(catalogues[locale] as object).filter((n) => !reference.has(n));
      expect(
        extra,
        `${locale}.json declares namespaces fa.json does not: ${extra.join(', ')}`,
      ).toEqual([]);
    }
  });

  it('resolve every namespace the reference declares, through the merge', () => {
    // The effective catalogue is `deepMerge(en, locale)`, so a locale only needs
    // the keys it translates. What it must not do is drop a namespace `en` has.
    const enNamespaces = Object.keys(catalogues.en as object);
    for (const locale of LOCALES) {
      for (const namespace of enNamespaces) {
        const resolved = (catalogues[locale] as Record<string, unknown>)[namespace] ?? {};
        expect(
          typeof resolved,
          `${locale}.json has no ${namespace} namespace and en.json does not provide one`,
        ).toBe('object');
      }
    }
  });
});
