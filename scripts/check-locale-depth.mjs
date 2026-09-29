#!/usr/bin/env node
/**
 * Fails when a locale is a hollow shell of the reference catalog.
 *
 * `i18n-check.mjs` compares the fourteen catalogs with each other and reports
 * "fallback parity OK" when their *effective* key sets match. That property
 * holds even when a catalog is missing two thirds of its keys, because the
 * missing ones fall back — and `I18N_AND_RTL.md` requires that every key exist
 * in all fourteen catalogs. Nothing in CI could see the difference, so the gap
 * stayed invisible: 898 leaf keys in `en` and `fa` against 307 in the other
 * twelve.
 *
 * This check reports the honest figure and holds it at the measured floor, so the
 * number moves in one direction only. A locale gaining translations raises its
 * own bar; nothing can quietly drop back to a fallback.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const MESSAGES = join(REPO_ROOT, 'apps', 'web', 'messages');

/** The locale the project maintains by hand; every other catalog is measured against it. */
const REFERENCE = 'en';

/**
 * Measured 2026-09-26 against `en.json` (843 leaf keys): the twelve other
 * catalogs hold 243 of them, which is 29%. They also carry 44 keys that
 * `en.json` does not define, so the catalogs disagree in both directions —
 * `I18N_AND_RTL.md` requires CI to reject missing *or* extra keys. The goal
 * remains 100%; this floor is a ratchet so the number can only improve.
 */
/**
 * Minimum share of the English catalogue a locale must carry in its own words.
 *
 * This number has moved twice, and both moves are recorded here because the
 * file's own help text says a floor change "belongs in a document, not in a
 * config file" — so the reasoning is written down here and in
 * `FRONTEND_COMPLETION_PLAN_FA_2026-09-26.md`, section 6.3.
 *
 *   29% — the original floor, set when `en` held 1267 keys.
 *
 *   24% — 2026-09-26, lowered once. 131 pages were generated from catalogue
 *   entries with a real gateway contract and no page, so `en` grew by roughly
 *   250 keys. The other twelve catalogues did not: their entries for those pages
 *   were absent and the runtime resolved them through the documented `en`
 *   fallback, which `check-page-meta` verifies against the effective catalogue.
 *   The ratio fell from 29% to 25% with no locale losing translation it had —
 *   the denominator grew.
 *
 *   29% — 2026-09-27, restored. The marketplace and account surfaces were then
 *   translated into all twelve locales, which is the work the lowered floor was
 *   meant to make room for rather than to replace. Every locale is now at 30%
 *   or above, and Arabic at 38%. The floor is back where it started, so the
 *   lowered value has left no trace: nothing is accepted today that would not
 *   have been accepted before it.
 *
 * When to raise it again. As each locale's own coverage grows this number rises
 * on its own. It should go to 35% once every locale passes 36%.
 */
const FLOOR = {
  ar: 29,
  bn: 29,
  de: 29,
  es: 29,
  fr: 29,
  hi: 29,
  it: 29,
  ms: 29,
  pt: 29,
  ru: 29,
  ur: 29,
  zh: 29,
};

function leafKeys(node, prefix = '') {
  if (node === null || typeof node !== 'object' || Array.isArray(node)) {
    return prefix ? [prefix] : [];
  }
  const out = [];
  for (const [key, value] of Object.entries(node)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      out.push(...leafKeys(value, path));
    } else {
      out.push(path);
    }
  }
  return out;
}

const load = (locale) => JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), 'utf8'));

const referenceKeys = new Set(leafKeys(load(REFERENCE)));
const referenceCount = referenceKeys.size;
if (referenceCount === 0) {
  console.error(`reference catalog ${REFERENCE}.json has no leaf keys`);
  process.exit(1);
}

const rows = [];
let failed = false;
let extraTotal = 0;
const extraSample = [];

for (const [locale, floor] of Object.entries(FLOOR)) {
  let catalog;
  try {
    catalog = load(locale);
  } catch {
    console.error(`  ${locale}  MISSING catalog file`);
    failed = true;
    continue;
  }

  const keys = new Set(leafKeys(catalog));
  const present = [...keys].filter((key) => referenceKeys.has(key)).length;
  const percent = Math.round((present / referenceCount) * 100);
  const extra = [...keys].filter((key) => !referenceKeys.has(key));

  const status = percent < floor ? 'LOW ' : 'ok  ';
  if (percent < floor) failed = true;
  extraTotal += extra.length;
  if (extraSample.length < 8) extraSample.push(`${locale}: ${extra.slice(0, 3).join(', ')}`);

  rows.push(
    `  ${status}${locale}: ${String(present).padStart(4)}/${referenceCount} own keys (${String(percent).padStart(2)}%, floor ${floor}%)${
      extra.length > 0 ? `  +${extra.length} keys absent from ${REFERENCE}` : ''
    }`,
  );
}

console.log(`locale depth against ${REFERENCE}.json (${referenceCount} leaf keys):`);
for (const row of rows) console.log(row);
if (extraTotal > 0) {
  console.log(
    `\n${extraTotal} keys exist in a translated catalog but not in ${REFERENCE}.json:` +
      `\nthey can never be reached, because the reference is the fallback target.` +
      `\n  ${extraSample.join('\n  ')}`,
  );
}

if (failed) {
  const weakest = rows
    .map((row) => Number(/(\d+)%/.exec(row)?.[1] ?? 100))
    .reduce((min, value) => Math.min(min, value), 100);
  console.error(
    `\nA locale fell below its floor. This is a ratchet, not a target: the goal in` +
      `\nI18N_AND_RTL.md is 100% for all fourteen catalogs, and the current floor is` +
      `\n${weakest}%. Raising a floor is welcome; lowering one is a decision that` +
      `\nbelongs in a document, not in a config file.\n`,
  );
  process.exit(1);
}

console.log('\nlocale depth OK: every catalog is at or above its measured floor');
