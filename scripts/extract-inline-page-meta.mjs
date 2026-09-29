#!/usr/bin/env node
/**
 * One-off migration aid: extract the inline `{fa, en}` title/description
 * dictionaries from the 53 public pages into a JSON file.
 *
 * The dictionaries are the last place in the app where visible copy bypasses the
 * message catalogue. A reader of `/zh/public/why` gets a Chinese navigation bar
 * around an English `<h1>`, because the heading came from
 * `TITLES[locale] ?? TITLES.en`. This script does not decide the fix; it only
 * lifts the existing strings out of the source so they can be placed in
 * `messages/<locale>.json` and then referenced with `getTranslations`.
 *
 * Run from the repository root:
 *   node scripts/extract-inline-page-meta.mjs
 */
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const APP = join(REPO_ROOT, 'apps', 'web', 'src', 'app', '[locale]');

/** `/public/why` -> `public-why`, so the catalogue key is stable and readable. */
function slugFor(file) {
  return relative(APP, dirname(file))
    .split('\\')
    .filter((segment) => segment && !segment.startsWith('(') && !segment.startsWith('['))
    .join('-')
    .replace(/-\d+$/, '')
    .replace(/\s+/g, '-');
}

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (name === 'page.tsx') acc.push(full);
  }
  return acc;
}

/**
 * Pull `fa: '…'` / `en: '…'` pairs out of a single-line object literal.
 *
 * The name is matched case-insensitively because the inventory is not uniform:
 * `public/science/evidence-base` declares lowercase `titles`/`descriptions`
 * while the other 52 use `TITLES`/`DESCRIPTIONS`. A case-sensitive scan misses
 * that page entirely, which is the same class of bug as the one being fixed.
 */
function readDict(source, name) {
  const re = new RegExp(`const ${name}:[^=]*= \\{([\\s\\S]*?)\\};`, 'im');
  const match = re.exec(source);
  if (!match) return null;
  const dict = {};
  const pairRe = /(fa|en):\s*'((?:[^'\\]|\\.)*)'/g;
  let entry;
  while ((entry = pairRe.exec(match[1])) !== null) dict[entry[1]] = entry[2];
  return Object.keys(dict).length > 0 ? dict : null;
}

const out = {};
const skipped = [];

for (const file of walk(APP)) {
  const source = readFileSync(file, 'utf8');
  const titles = readDict(source, 'TITLES');
  const descriptions = readDict(source, 'DESCRIPTIONS');
  if (!titles && !descriptions) continue;

  const slug = slugFor(file);
  out[slug] = {
    path: `/${relative(APP, dirname(file)).split('\\').join('/')}`,
    title: titles ?? null,
    description: descriptions ?? null,
  };
  if (!titles?.fa || !titles?.en) skipped.push(`${slug}: incomplete TITLES`);
  if (!descriptions?.fa || !descriptions?.en) skipped.push(`${slug}: incomplete DESCRIPTIONS`);
}

const sorted = Object.fromEntries(Object.entries(out).sort(([a], [b]) => a.localeCompare(b)));
writeFileSync(join(REPO_ROOT, '.tmp', 'inline-page-meta.json'), `${JSON.stringify(sorted, null, 2)}\n`, 'utf8');

console.log(`extracted ${Object.keys(sorted).length} pages`);
if (skipped.length > 0) {
  console.log(`\nincomplete extractions (${skipped.length}):`);
  for (const note of skipped) console.log(`  - ${note}`);
}
console.log('\nkeys:');
for (const [slug, value] of Object.entries(sorted)) {
  console.log(`  ${slug.padEnd(38)} ${value.title?.en ?? '—'}`);
}
