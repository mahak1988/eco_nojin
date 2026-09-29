#!/usr/bin/env node
/**
 * Fails when a locale catalog contains text that is not in its own script.
 *
 * The other two i18n gates check *structure*: `i18n-check.mjs` verifies that the
 * effective key sets match, and `check-locale-depth.mjs` holds each catalog at a
 * ratchet of translated keys. Both properties are satisfied by a catalog whose
 * values are not readable text in the language it claims to be. On 2026-09-26
 * seven of the fourteen catalogs (`bn`, `hi`, `it`, `ms`, `pt`, `ru`, `zh`) were
 * byte-identical files holding UTF-8 double-encoded mojibake rendered in Arabic
 * presentation forms. A reader using a screen reader in any of those seven
 * languages received a wall of unreadable characters, and both structural gates
 * reported "OK".
 *
 * This gate is the one that can see it. It makes two independent checks:
 *
 *   1. Mojibake detection. Classic UTF-8-as-cp1256 artefacts are literal
 *      sequences. Any of them means a file was written through the wrong codec.
 *   2. Script affinity. Each locale declares the Unicode ranges its script
 *      actually uses, and a share of its own letters must fall inside them.
 *      Transliterated or loanword copy is allowed; a catalog that is entirely
 *      English will not pass for `ru`.
 *
 * The reference catalogs `fa` and `en` are exempt from the affinity check: `en`
 * is the source language and `fa` is the fallback target of the merge chain.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
/**
 * Overridable so the gate can be run against a deliberately corrupted copy in a
 * test. A gate that has never been observed failing is a gate of unknown
 * correctness: this one was written to catch seven byte-identical mojibake
 * catalogs and reported "OK" on the day it was written, because the code had
 * already been fixed. `apps/web/src/lib/i18n/gate-negative.test.ts` uses this to
 * prove it still fires.
 */
const MESSAGES = process.env.ECO_MESSAGES_DIR ?? join(REPO_ROOT, 'apps', 'web', 'messages');

/**
 * Characters that survive a UTF-8 → cp1256/Windows-1252 round trip. They are
 * never legitimate output of a JSON file written by a UTF-8 toolchain, so one
 * occurrence is a hard failure rather than a ratio.
 */
const MOJIBAKE_MARKERS = [
  'ط§', // ARABIC LETTER ALEF WITH ATTACHED FATHA — the `ظ` family
  'ط±',
  'ط®',
  'ظ†',
  'ظ‡',
  'ظˆ', // ARABIC LETTER ALEF WITH ATTACHED FATHA on a beh
  'â€”', // em dash
  'â€“',
  'â€¢', // middle dot
  'â€¦', // ellipsis
  'â€˜',
  'â€™', // right single quote
  'Ã©', // é
  'Ã¨',
  'Ã¼',
  'Ã¶',
  'Ã¤',
  'Ã±',
  'Â«', // «
  'Â»', // »
  'Â«',
  'Ø ±', // Ø from a mis-decoded ± 0
  'ï¿½', // replacement char as three bytes
  '�', // lone replacement character
];

/**
 * Unicode ranges that legitimately carry each locale's own letters.
 * Latin script is deliberately absent: transliteration and loanwords are normal
 * in every one of these languages, and the mojibake marker check already covers
 * the failure this affinity rule is here to catch.
 */
const SCRIPT_RANGES = {
  bn: [
    [0x0980, 0x09ff], // Bengali
    [0x200c, 0x200d], // ZWNJ/ZWJ
  ],
  hi: [
    [0x0900, 0x097f], // Devanagari
    [0x200c, 0x200d],
  ],
  ru: [
    [0x0400, 0x04ff], // Cyrillic
    [0x200c, 0x200d],
  ],
  zh: [
    [0x4e00, 0x9fff], // CJK Unified Ideographs
    [0x3400, 0x4dbf], // Extension A
    [0x3000, 0x303f], // CJK punctuation
    [0xff00, 0xffef], // Fullwidth forms
  ],
};

const ARABIC_RANGE = [0x0600, 0x06ff];
const ARABIC_PRESENTATION = [0xfb50, 0xfdff];
const ARABIC_SUPPLEMENT = [0x0750, 0x077f];
const EXTENDED_PICTOGRAPHIC = [0x1f300, 0x1f9ff];

const inRanges = (code, ranges) => ranges.some(([lo, hi]) => code >= lo && code <= hi);

/** Locales whose script is Arabic-script. `fa` and `en` are handled separately. */
const ARABIC_SCRIPT_LOCALES = ['ar', 'ur'];

/**
 * Minimum share of the catalog's own letters that must be in the locale's
 * script. Measured 2026-09-26 on the real `ar` and `ur` catalogs: Arabic script
 * carries the large majority of letters, with Latin transliteration and English
 * loanwords making up the rest. The floor is set below both measurements.
 */
const MIN_SCRIPT_SHARE = {
  bn: 0.4,
  hi: 0.4,
  ru: 0.3,
  zh: 0.4,
  ar: 0.6,
  ur: 0.5,
};

/**
 * Locales that must be Latin-script. They carry no script affinity rule, but
 * they are still checked for mojibake and for a copy-paste of the source
 * language: `it`, `ms`, `pt`, `de`, `es`, `fr` are Latin, so a value that is
 * wholly Arabic presentation forms is a defect no ratio can hide.
 */
const LATIN_SCRIPT_LOCALES = ['de', 'es', 'fr', 'it', 'ms', 'pt'];

function collectStrings(node, out = []) {
  if (typeof node === 'string') {
    out.push(node);
  } else if (Array.isArray(node)) {
    for (const item of node) collectStrings(item, out);
  } else if (node !== null && typeof node === 'object') {
    for (const value of Object.values(node)) collectStrings(value, out);
  }
  return out;
}

const load = (locale) => JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), 'utf8'));

const locales = process.argv.slice(2).length > 0 ? process.argv.slice(2) : Object.keys(SCRIPT_RANGES).concat(ARABIC_SCRIPT_LOCALES, LATIN_SCRIPT_LOCALES);

const errors = [];
const rows = [];

for (const locale of locales) {
  let catalog;
  try {
    catalog = load(locale);
  } catch {
    errors.push(`${locale}: catalog file is missing or is not valid JSON`);
    continue;
  }

  const strings = collectStrings(catalog);
  if (strings.length === 0) {
    errors.push(`${locale}: catalog contains no strings at all`);
    continue;
  }

  // --- 1. Mojibake markers -------------------------------------------------
  const markerHits = [];
  for (const value of strings) {
    for (const marker of MOJIBAKE_MARKERS) {
      if (value.includes(marker)) {
        markerHits.push(marker);
        break;
      }
    }
  }
  if (markerHits.length > 0) {
    const unique = [...new Set(markerHits)];
    errors.push(
      `${locale}: ${markerHits.length}/${strings.length} strings contain mojibake markers (${unique.slice(0, 6).join(' ')}). ` +
        `The file was written through the wrong codec; rewrite it as UTF-8.`,
    );
  }

  // --- 2. Script affinity --------------------------------------------------
  let own = 0;
  let letters = 0;
  for (const value of strings) {
    for (const char of value) {
      const code = char.codePointAt(0);
      if (code < 0x41) continue; // digits, punctuation, ASCII control
      letters += 1;
      if (SCRIPT_RANGES[locale]) {
        if (inRanges(code, SCRIPT_RANGES[locale])) own += 1;
      } else if (ARABIC_SCRIPT_LOCALES.includes(locale)) {
        if (
          inRanges(code, [ARABIC_RANGE, ARABIC_PRESENTATION, ARABIC_SUPPLEMENT]) ||
          inRanges(code, [EXTENDED_PICTOGRAPHIC])
        ) {
          own += 1;
        }
      } else if (LATIN_SCRIPT_LOCALES.includes(locale)) {
        if (inRanges(code, [[ARABIC_RANGE, ARABIC_PRESENTATION, ARABIC_SUPPLEMENT]])) own += 0; // counted as wrong below
      }
    }
  }

  if (SCRIPT_RANGES[locale] || ARABIC_SCRIPT_LOCALES.includes(locale)) {
    const floor = MIN_SCRIPT_SHARE[locale];
    const share = letters === 0 ? 0 : own / letters;
    if (share < floor) {
      errors.push(
        `${locale}: only ${(share * 100).toFixed(1)}% of its letters are in its own script (floor ${(floor * 100).toFixed(0)}%). ` +
          `Either the catalog is untranslated, or it was transcoded.`,
      );
    }
    rows.push(
      `  ${locale.padEnd(4)} script affinity ${(share * 100).toFixed(1).padStart(5)}% (floor ${(floor * 100).toFixed(0)}%)` +
        `${markerHits.length > 0 ? `   mojibake: ${markerHits.length} strings` : ''}`,
    );
  } else {
    // Latin locales: any Arabic presentation form is a defect.
    let arabic = 0;
    for (const value of strings) {
      for (const char of value) {
        const code = char.codePointAt(0);
        if (inRanges(code, [ARABIC_RANGE, ARABIC_PRESENTATION, ARABIC_SUPPLEMENT])) arabic += 1;
      }
    }
    if (arabic > 0) {
      errors.push(
        `${locale}: ${arabic} Arabic-script characters found in a Latin-script catalog. ` +
          `This is the signature of a copied Persian file rather than a translation.`,
      );
    }
    rows.push(
      `  ${locale.padEnd(4)} Latin script` + `${markerHits.length > 0 ? `   mojibake: ${markerHits.length} strings` : ''}`,
    );
  }
}

console.log('locale encoding and script affinity:');
for (const row of rows) console.log(row);

if (errors.length > 0) {
  console.error(`\nlocale encoding check failed with ${errors.length} problem(s):`);
  for (const error of errors) console.error(`  - ${error}`);
  console.error(
    `\nA locale catalog must contain readable text in the language it claims to be.` +
      `\nStructural gates cannot see this: a byte-identical copy of one broken file` +
      `\nsatisfies key parity and depth ratchets in all fourteen locales.`,
  );
  process.exit(1);
}

console.log('\nlocale encoding OK: every catalog is readable text in its own script');
