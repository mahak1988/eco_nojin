/**
 * ICU MessageFormat placeholder parity across all catalogues.
 *
 * A translated catalogue that renames or drops an ICU placeholder is not a lint
 * warning; it is a runtime failure inside next-intl, in the language the reader
 * is least able to work around. Key parity and the depth ratchet cannot see it:
 * `admin.grid.results` in every locale has the same key and the same length.
 *
 * This check walks every leaf of every catalogue and asserts that, per key path,
 * the set of `{placeholder}` names and the set of plural/select category names
 * match the English source exactly.
 *
 * Run: node scripts/check-icu-placeholders.mjs
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const MESSAGES = join(REPO_ROOT, 'apps', 'web', 'messages');

const REFERENCE = 'en';

/**
 * ICU argument: `{name}` or `{name, plural, ...}` or `{name, select, ...}`.
 *
 * A plain regex over the whole string mis-parses any message whose plural branch
 * body opens with a category word. `one {One input field is not valid…}` — the
 * English copy of a tool-validation message — yields a phantom `One:simple`
 * argument from the word "One" inside the branch, while the Persian translation
 * of the same key does not, because its branch opens with a Persian letter. The
 * gate then reports a structural difference between two identical structures and
 * invites someone to "fix" a correct translation.
 *
 * So arguments are collected at brace depth 0 only. A `{` that opens a branch
 * body is consumed as nesting, not as the start of an argument.
 */
const ARGUMENT_AT_TOP = /\{\s*([A-Za-z0-9_]+)\s*(?:,\s*(plural|select|selectordinal)\b)?/g;

function argumentsOf(text) {
  const found = [];
  let depth = 0;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '{') {
      if (depth === 0) {
        ARGUMENT_AT_TOP.lastIndex = i;
        const match = ARGUMENT_AT_TOP.exec(text);
        if (match) {
          found.push(`${match[1]}:${match[2] ?? 'simple'}`);
          // Skip past the argument's own header so its body is not rescanned.
          i = ARGUMENT_AT_TOP.lastIndex - 1;
        }
      }
      depth += 1;
    } else if (char === '}') {
      depth -= 1;
    }
  }
  return found;
}

/** A plural/select block body: `one {...} other {...}` — names, not argument names. */
const CATEGORY = /(?:^|[\s{}])(zero|one|two|few|many|other)\s*\{/g;

function flatten(node, prefix = '', out = {}) {
  for (const [key, value] of Object.entries(node)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) flatten(value, path, out);
    else out[path] = value;
  }
  return out;
}

/** Placeholder names and plural/select category names inside one string. */
function signature(value) {
  const strings = Array.isArray(value) ? value : [value];
  const args = new Set();
  const cats = new Set();
  for (const s of strings) {
    if (typeof s !== 'string') continue;
    for (const a of argumentsOf(s)) args.add(a);
    for (const m of s.matchAll(CATEGORY)) cats.add(m[1]);
  }
  return { args: [...args].sort(), cats: [...cats].sort() };
}

const load = (locale) => {
  const raw = readFileSync(join(MESSAGES, `${locale}.json`), 'utf8');
  return JSON.parse(raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw);
};

const reference = flatten(load(REFERENCE));
const locales = readdirSync(MESSAGES)
  .filter((file) => file.endsWith('.json'))
  .map((file) => file.replace('.json', ''))
  .filter((locale) => locale !== REFERENCE);

const errors = [];

for (const locale of locales) {
  const catalog = flatten(load(locale));
  let checked = 0;
  for (const [path, value] of Object.entries(reference)) {
    if (!(path in catalog)) continue; // absence is check-locale-depth's business
    if (!/\{/.test(String(value))) continue;
    checked++;
    const want = signature(value);
    const got = signature(catalog[path]);
    if (want.args.join(',') !== got.args.join(',')) {
      errors.push(
        `${locale} ${path}: placeholders [${got.args.join(', ')}] do not match en [${want.args.join(', ')}]`,
      );
    }
    if (want.cats.join(',') !== got.cats.join(',')) {
      errors.push(
        `${locale} ${path}: plural/select categories [${got.cats.join(', ')}] do not match en [${want.cats.join(', ')}]`,
      );
    }
  }
  console.log(`  ${locale.padEnd(4)} ${checked} ICU-bearing key(s) checked`);
}

console.log(`\nICU placeholder parity against ${REFERENCE}.json (${Object.keys(reference).length} leaf keys):`);

if (errors.length > 0) {
  console.error(`\nplaceholder parity failed with ${errors.length} problem(s):`);
  for (const error of errors) console.error(`  - ${error}`);
  console.error(
    `\nA renamed or dropped placeholder is a runtime crash in next-intl, not a lint\n` +
      `warning, and it happens in the language a reader is least able to work around.\n`,
  );
  process.exit(1);
}

console.log('\nplaceholder parity OK: every argument name and plural category matches en');
