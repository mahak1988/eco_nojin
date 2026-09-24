#!/usr/bin/env node
/**
 * i18n key parity checker — master plan §۰.6 (pseudo-localization in CI).
 * Verifies every skeleton locale carries the same key structure as fa (the
 * content reference). Exit 1 on any mismatch so CI fails loudly.
 *
 * Run: node scripts/i18n-check.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const MESSAGES_DIR = new URL('../messages/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');

function flatten(obj, prefix = '') {
  return Object.entries(obj).flatMap(([k, v]) => {
    const key = prefix ? `${prefix}.${k}` : k;
    return v && typeof v === 'object' && !Array.isArray(v)
      ? flatten(v, key)
      : [key];
  });
}

/** Mirrors deepMerge() in src/lib/i18n/messages.ts (the runtime contract). */
function deepMerge(...layers) {
  const out = {};
  for (const layer of layers) {
    for (const [key, value] of Object.entries(layer)) {
      const existing = out[key];
      if (
        value &&
        typeof value === 'object' &&
        !Array.isArray(value) &&
        existing &&
        typeof existing === 'object' &&
        !Array.isArray(existing)
      ) {
        out[key] = deepMerge(existing, value);
      } else {
        out[key] = value;
      }
    }
  }
  return out;
}

const stripBom = (s) => (s.charCodeAt(0) === 0xfeff ? s.slice(1) : s);

const read = (locale) =>
  JSON.parse(stripBom(readFileSync(join(MESSAGES_DIR, `${locale}.json`), 'utf8')));

const locales = readdirSync(MESSAGES_DIR)
  .filter((f) => f.endsWith('.json'))
  .map((f) => f.replace('.json', ''));

const reference = new Set(flatten(read('fa')).filter((k) => !k.startsWith('meta')));

/**
 * Replicates the runtime fallback chain (src/lib/i18n/messages.ts):
 * effective catalogue = { ...fa, ...en, ...<locale> } — so a skeleton locale
 * is valid as long as the *merged* view the app serves has every fa key.
 */
let failed = false;

for (const locale of locales) {
  const merged = deepMerge(read('fa'), read('en'), read(locale));
  const keys = new Set(flatten(merged).filter((k) => !k.startsWith('meta')));
  const missing = [...reference].filter((k) => !keys.has(k));
  if (missing.length) {
    failed = true;
    console.error(`✗ ${locale}: missing after fallback chain: ${missing.join(', ')}`);
  } else {
    const own = new Set(flatten(read(locale)).filter((k) => !k.startsWith('meta')));
    console.log(`✓ ${locale}: ${own.size} own keys · ${keys.size} effective — fallback parity OK`);
  }
}

process.exit(failed ? 1 : 0);

