/**
 * Merge i18n fragments into the locale catalogues.
 *
 * ## Why fragments exist
 *
 * Fourteen JSON files, one per locale, is a single-writer format. It works when
 * one agent or one person edits translations, and it fails the moment several
 * do: each context reads the whole catalogue, adds its keys, and writes the
 * whole file back, so the last writer silently discards everyone else's keys.
 * That is not a merge conflict git can see — it is a lost write inside one file,
 * and it is exactly what happens if an admin-pages agent and a marketplace agent
 * run at the same time.
 *
 * So a context owns a *fragment* — its own file, its own key namespace, nobody
 * else writes it — and this script merges fragments into the catalogues. The
 * merge is additive and refuses to overwrite an existing key, so a fragment that
 * disagrees with a hand-edited catalogue fails loudly instead of winning by
 * arriving last.
 *
 * ## Contract
 *
 *   apps/web/src/i18n/fragments/<context>.json
 *
 * where `<context>` is the owning context slug, and the file is
 *
 *   { "<locale>": { <key>: <value>, … }, … }
 *
 * A context may appear in every locale it supports. A locale absent from a
 * fragment simply does not receive that context's keys, and the existing
 * fallback chain covers it — that is how the depth ratchet in
 * `check-locale-depth.mjs` keeps working.
 *
 * ## Usage
 *
 *   node scripts/merge-i18n-fragments.mjs            # merge, then report
 *   node scripts/merge-i18n-fragments.mjs --check    # report only, exit 1 on drift
 *
 * `--check` is the form a gate should use: it fails when the catalogues are not
 * in sync with the fragments, so a fragment can never be committed and then
 * forgotten.
 */
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = join(dirname(dirname(fileURLToPath(import.meta.url))));
const WEB = join(REPO, 'apps', 'web');
const FRAGMENT_DIR = join(WEB, 'src', 'i18n', 'fragments');
const MESSAGES = join(WEB, 'messages');

const CHECK_ONLY = process.argv.includes('--check');

/** Depth-first flatten, so a nested fragment and a flat catalogue compare equal. */
function flatten(object, prefix = '', out = {}) {
  for (const [key, value] of Object.entries(object ?? {})) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) flatten(value, path, out);
    else out[path] = value;
  }
  return out;
}

/** Inverse of flatten, so a flat map can be written back as a nested catalogue. */
function nest(flat) {
  const out = {};
  for (const [path, value] of Object.entries(flat)) {
    const parts = path.split('.');
    let cursor = out;
    for (let i = 0; i < parts.length - 1; i += 1) {
      cursor[parts[i]] ??= {};
      cursor = cursor[parts[i]];
    }
    cursor[parts.at(-1)] = value;
  }
  return out;
}

if (!existsSync(FRAGMENT_DIR)) {
  console.log('no fragment directory; nothing to merge');
  process.exit(0);
}

const fragmentFiles = readdirSync(FRAGMENT_DIR).filter((n) => n.endsWith('.json'));
if (fragmentFiles.length === 0) {
  console.log('no fragments; nothing to merge');
  process.exit(0);
}

const localeFiles = readdirSync(MESSAGES).filter((n) => n.endsWith('.json'));
const catalogues = new Map();
for (const file of localeFiles) {
  const locale = file.replace(/\.json$/, '');
  // A Map, not the plain object `flatten` returns — the merge tests membership
  // with `.has`, which an object does not have.
  catalogues.set(locale, new Map(Object.entries(flatten(JSON.parse(readFileSync(join(MESSAGES, file), 'utf8'))))));
}

/** context -> locale -> flat keys */
const fragments = new Map();
for (const file of fragmentFiles) {
  const context = file.replace(/\.json$/, '');
  const parsed = JSON.parse(readFileSync(join(FRAGMENT_DIR, file), 'utf8'));
  fragments.set(context, parsed);
}

/**
 * Deep value equality.
 *
 * `!==` compares arrays by reference, so two array-valued keys with identical
 * contents always looked like a conflict — a false positive on every plural or
 * list string in a fragment, which is most of them. A gate that cries wolf is a
 * gate people learn to skip, so this compares by value.
 */
function sameValue(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (a === null || b === null) return false;
  if (typeof a !== 'object') return false;
  return JSON.stringify(a) === JSON.stringify(b);
}

let added = 0;
const conflicts = [];
const plan = new Map();

for (const [context, byLocale] of fragments) {
  for (const [locale, tree] of Object.entries(byLocale)) {
    if (!catalogues.has(locale)) {
      conflicts.push(`${context}: locale "${locale}" has no catalogue at messages/${locale}.json`);
      continue;
    }
    const flat = flatten(tree);
    const catalogue = catalogues.get(locale);
    const target = plan.get(locale) ?? new Map();
    for (const [key, value] of Object.entries(flat)) {
      const namespaced = key.includes('.') ? key : `${context}.${key}`;
      if (catalogue.has(namespaced)) {
        if (!sameValue(catalogue.get(namespaced), value)) {
          conflicts.push(
            `${context}: ${locale} "${namespaced}" already exists with a different value. ` +
              `A fragment does not overwrite a hand-edited catalogue — resolve it by hand.`,
          );
        }
        continue;
      }
      if (target.has(namespaced) && !sameValue(target.get(namespaced), value)) {
        conflicts.push(`${context}: two fragments disagree on ${locale} "${namespaced}"`);
        continue;
      }
      target.set(namespaced, value);
      added += 1;
    }
    plan.set(locale, target);
  }
}

for (const [locale, keys] of plan) {
  const merged = new Map(catalogues.get(locale));
  for (const [key, value] of keys) merged.set(key, value);
  // A fragment is owned by one context, so nesting it back under the context
  // slug keeps the catalogue's per-context layout. Keys that already carried a
  // dot are written where the fragment said they belong.
  const tree = {};
  for (const [key, value] of merged) {
    const parts = key.split('.');
    let cursor = tree;
    for (let i = 0; i < parts.length - 1; i += 1) {
      cursor[parts[i]] ??= {};
      cursor = cursor[parts[i]];
    }
    cursor[parts.at(-1)] = value;
  }
  if (!CHECK_ONLY) {
    const target = join(MESSAGES, `${locale}.json`);
    const existing = readFileSync(target, 'utf8');
    writeFileSync(target, `${JSON.stringify(tree, null, 2)}\n`, 'utf8');
    void existing;
  }
}

const contexts = [...fragments.keys()].sort();
console.log(`fragments: ${contexts.length} — ${contexts.join(', ')}`);
console.log(`catalogues: ${catalogues.size}`);
console.log(`keys merged: ${added}${CHECK_ONLY ? ' (check mode: not written)' : ''}`);

if (conflicts.length > 0) {
  console.error(`\n${conflicts.length} conflict(s):`);
  for (const c of conflicts) console.error(`  ${c}`);
  process.exit(1);
}

if (CHECK_ONLY && added > 0) {
  console.error(
    `\n${added} key(s) exist in a fragment but not in the catalogues. ` +
      `Run without --check to merge, then commit the catalogues with the fragment.`,
  );
  process.exit(1);
}

console.log('fragments and catalogues are in sync');
