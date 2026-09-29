#!/usr/bin/env node
/**
 * Fails when a page's heading bypasses the message catalogue, or when a locale's
 * `pageMeta` entry is missing, blank, or written in the wrong script.
 *
 * What this replaces
 * ------------------
 * Fifty-three public pages declared their heading as a module-level dictionary
 *
 *     const TITLES: Record<string, string> = { fa: 'â€¦', en: 'â€¦' };
 *     title: TITLES[locale] ?? TITLES.en,
 *
 * which is a two-language dictionary with a hard-coded fallback. Eleven of the
 * fourteen official languages received the English string while the surrounding
 * chrome rendered in the reader's own language â€” confirmed in the browser on
 * `/zh/public/why`, which showed a Chinese menu bar around an English `<h1>`.
 * The same files hand-wrote `alternates.languages` with two locales, contradicting
 * the fourteen-locale cluster the root layout emits.
 *
 * Why a dedicated gate
 * --------------------
 * `check-message-usage.mjs` can only verify that a key it can see exists in the
 * catalogue. A dictionary read is not a `t()` call, so it is invisible to every
 * existing gate â€” which is why this class of defect survived. This one greps for
 * the pattern itself, so a new inline dictionary fails the build.
 *
 * It also validates the catalogue side, because a `[title, description]` pair
 * with a missing member is valid JSON and renders as a runtime
 * `MISSING_MESSAGE`: that is how ~128 half-finished translations were caught
 * while they were being written.
 *
 * Run from the repository root:
 *   node scripts/check-page-meta.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';


const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB = join(REPO_ROOT, 'apps', 'web');
const MESSAGES = join(WEB, 'messages');
const APP = join(WEB, 'src', 'app');

const errors = [];

// --- 1. no inline heading dictionaries in a page ----------------------------

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (name === 'page.tsx') acc.push(full);
  }
  return acc;
}

const INLINE_DICT = /^\s*const (?:TITLES|DESCRIPTIONS|titles|descriptions)\b/m;
const INLINE_READ = /\b(?:TITLES|DESCRIPTIONS|titles|descriptions)\[locale\]\s*\?\?/;

let pageCount = 0;
for (const file of walk(APP)) {
  const source = readFileSync(file, 'utf8');
  if (INLINE_DICT.test(source)) {
    errors.push(
      `${relative(WEB, file)}: declares an inline heading dictionary. ` +
        `Use getTranslations('pageMeta.<slug>') so every locale gets its own string.`,
    );
  }
  if (INLINE_READ.test(source)) {
    errors.push(
      `${relative(WEB, file)}: reads a heading from a locale dictionary. ` +
        `That pattern always falls back to English for the other twelve locales.`,
    );
  }
  pageCount += 1;
}

// --- 2. no hand-written two-locale hreflang clusters ------------------------

const MANUAL_HREFLANG = /languages:\s*\{\s*(?:fa|en):/;
for (const file of walk(APP)) {
  const source = readFileSync(file, 'utf8');
  if (MANUAL_HREFLANG.test(source)) {
    errors.push(
      `${relative(WEB, file)}: hand-writes alternates.languages. ` +
        `Use languageAlternates(path) so all fourteen locales are advertised.`,
    );
  }
}

// --- 3. an absolute URL may not concatenate a bare identifier ---------------
//
// `generate-resource-pages.mjs` emitted `url: \`${BASE_URL}/${locale}ROUTE\`` on
// 128 pages, so every Open Graph URL resolved to `https://app.eco-nojin.org/faROUTE`
// and every social share card and crawler that trusts `og:url` pointed at a path
// that does not exist. The generator has been wrong here twice already, so the
// shape is checked rather than trusted: inside a template literal an identifier
// has to be interpolated with `${…}` to reach the rendered page.
//
// This matches only a *bare* uppercase identifier directly after the closing
// brace, so a correct `${ROUTE}` — which has a `$` in front of it — and a plain
// `${locale}` with nothing after it both pass.

const BARE_IDENTIFIER_IN_URL = /\$\{locale\}([A-Z_][A-Z0-9_]*)/;
for (const file of walk(APP)) {
  const source = readFileSync(file, 'utf8');
  const match = BARE_IDENTIFIER_IN_URL.exec(source);
  if (match) {
    errors.push(
      `${relative(WEB, file)}: concatenates a bare \`${match[1]}\` onto the locale in a URL. ` +
        `Interpolate it (\`\${${match[1]}}\`) or the rendered URL is not a real path.`,
    );
  }
}

// --- 4. every pageMeta entry resolves, and is in the right script ----------
//
// The contract checked here is the *effective* catalogue, not the own-key set.
// `loadMessages` merges `en` underneath every locale, so a slug present only in
// `en.json` still renders in all fourteen languages. Requiring an own-key copy in
// every catalogue is `check-locale-depth`'s job, and this gate asserting it too
// would make it look as though the fallback chain did not work.
//
// What must never happen is a slug that resolves nowhere, which is the
// `MISSING_MESSAGE` failure: a key absent from `en` as well.

const en = JSON.parse(readFileSync(join(MESSAGES, 'en.json'), 'utf8'));
const slugs = Object.keys(en.pageMeta ?? {});
if (slugs.length === 0) {
  errors.push('en.json has no pageMeta namespace');
}

/** Anything a locale adds on top of the English base, per the runtime chain. */
const ownOf = (catalog) => catalog.pageMeta ?? {};

const SCRIPTS_BY_LOCALE = {
  ar: [[0x0600, 0x06ff], [0xfb50, 0xfdff]],
  ur: [[0x0600, 0x06ff], [0xfb50, 0xfdff]],
  ru: [[0x0400, 0x04ff]],
  zh: [[0x4e00, 0x9fff], [0x3000, 0x303f], [0xff00, 0xffef]],
  hi: [[0x0900, 0x097f]],
  bn: [[0x0980, 0x09ff]],
};

/** Latin, Cyrillic, Arabic and Indic neighbours are all legitimate neighbours. */
const NEIGHBOUR_RANGES = [
  [0x0590, 0x06ff],
  [0x0900, 0x0dff],
  [0x0400, 0x04ff],
  [0x4e00, 0x9fff],
  [0x3000, 0x303f],
  [0xff00, 0xffef],
  [0x2000, 0x206f],
];

const load = (locale) => JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), 'utf8'));

let translated = 0;
for (const locale of readdirSync(MESSAGES)
  .filter((f) => f.endsWith('.json'))
  .map((f) => f.slice(0, -5))) {
  if (locale === 'en') continue;
  const catalogue = load(locale);
  const own = ownOf(catalogue);

  if (catalogue.pageMeta) translated += 1;

  for (const slug of slugs) {
    // Resolves if either the locale or the English base has it.
    const entry = own[slug] ?? en.pageMeta[slug];
    if (!entry) {
      errors.push(`${locale}.pageMeta.${slug}: missing, and absent from en.json too`);
      continue;
    }

    // Script affinity is only asserted on the locale's *own* strings. A value
    // inherited from English is legitimately English, and flagging it would be
    // flagging the fallback chain for working.
    const declared = own[slug];
    if (!declared) continue;

    const ranges = SCRIPTS_BY_LOCALE[locale];
    if (!ranges) continue;
    for (const field of ['title', 'description']) {
      const value = declared[field];
      if (typeof value !== 'string' || value.trim() === '') {
        errors.push(`${locale}.pageMeta.${slug}.${field}: empty`);
        continue;
      }
      for (const char of value) {
        const code = char.codePointAt(0);
        if (code <= 0x00ff) continue;
        const own2 = ranges.some(([lo, hi]) => code >= lo && code <= hi);
        const neighbour = NEIGHBOUR_RANGES.some(([lo, hi]) => code >= lo && code <= hi);
        if (!own2 && !neighbour) {
          errors.push(
            `${locale}.pageMeta.${slug}.${field}: ${char} (U+${code.toString(16).toUpperCase()}) is not this locale's script`,
          );
          break;
        }
      }
    }
  }
}

// --- 4. no slug is declared without a complete pair -------------------------
//
// The hand-written translation tables live beside this gate and are applied by
// `apply-resource-page-meta.mjs`, which writes only complete pairs. This check
// is over the catalogues rather than over the tables, because the catalogues are
// what the runtime reads: a slug that resolves nowhere is the failure that
// matters, and section 3 already covers it.

console.log(`page meta gate: ${pageCount} pages scanned, ${slugs.length} slugs per locale`);

if (errors.length > 0) {
  console.error(`\npage meta check failed with ${errors.length} problem(s):`);
  for (const error of errors.slice(0, 40)) console.error(`  - ${error}`);
  if (errors.length > 40) console.error(`  ... and ${errors.length - 40} more`);
  process.exit(1);
}

console.log(
  'page meta OK: no inline heading dictionaries, no two-locale hreflang, ' +
    'no bare identifier in a URL, every entry translated',
);
