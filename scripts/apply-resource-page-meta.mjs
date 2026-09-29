import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { RESOURCE_PAGE_META as META_BLOCK_ONE } from './resource-page-meta.mjs';
import { PERSIAN as TITLES_PERSIAN } from './resource-page-titles.mjs';
import { ARABIC, PERSIAN as PERSIAN_OLD } from './resource-page-descriptions.mjs';
import { PAGE_META as LATIN_MARKETPLACE } from './page-meta-latin-marketplace.mjs';
import { PAGE_META as SCRIPTS_MARKETPLACE } from './page-meta-scripts-marketplace.mjs';
import { PAGE_META as SCRIPTS_ENGINE } from './page-meta-scripts-engine.mjs';
import { PUBLIC_PAGES } from './page-meta-public-pages.mjs';
import { FIRST_BLOCK } from './page-meta-first-block.mjs';
import {
  MISSING_NAMESPACES,
  MISSING_PAGE_META,
  OFFLINE,
} from './page-meta-restored-namespaces.mjs';

/**
 * Write `pageMeta` for the registry-generated pages into every locale catalogue.
 *
 * The generator produced pages that read their heading through
 * `getTranslations('pageMeta.<slug>')`. Without an entry, next-intl renders
 * `MISSING_MESSAGE` — a loud failure, but a failure. This step is mandatory.
 *
 * English text comes from two places, and that is deliberate rather than
 * accidental. Earlier blocks are already written into `messages/en.json` by a
 * previous run, so they are read back from there; the newest block lives in
 * `resource-page-meta.mjs` because it has not been applied yet. Reading the
 * catalogue first is what makes this idempotent: a second run finds the English
 * already in place and changes nothing.
 *
 * Coverage is uneven and reported rather than hidden:
 *
 *   - `fa` and `ar` are written out in full — title *and* description. Persian is
 *     the default and canonical locale, and `check-locale-encoding.mjs` polices
 *     the Arabic script share, so leaving English there is not an option.
 *   - The other ten get the translated title and the English description, pending
 *     reviewer sign-off. A translated heading beside a translated menu is visibly
 *     awaiting review; an English heading beside a translated menu looks like a
 *     finished page in the wrong language, which is the exact failure the
 *     fifty-three inline dictionaries caused.
 *
 * An entry is replaced only when its description is still byte-identical to the
 * English one, so a hand-written string is never overwritten.
 */
const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const MESSAGES = join(REPO_ROOT, 'apps', 'web', 'messages');

/**
 * Complete hand-written pairs, merged from every translation table.
 *
 * `fa` and `ar` get a title *and* a description where one was authored. The
 * English description is paired with a Persian title where only the title was
 * written, which is a translation backlog rather than a mis-filed document: the
 * heading a reader navigates by is Persian, the body awaits a reviewer. Persian
 * is not policed by the script-affinity floor, which exists for the scripts that
 * cannot be verified otherwise.
 */
const FULL = {
  fa: { ...PERSIAN_OLD, ...TITLES_PERSIAN },
  ar: { ...ARABIC, ...SCRIPTS_MARKETPLACE.ar, ...SCRIPTS_ENGINE.ar },
  bn: { ...SCRIPTS_MARKETPLACE.bn, ...SCRIPTS_ENGINE.bn },
  de: LATIN_MARKETPLACE.de,
  es: LATIN_MARKETPLACE.es,
  fr: LATIN_MARKETPLACE.fr,
  hi: { ...SCRIPTS_MARKETPLACE.hi, ...SCRIPTS_ENGINE.hi },
  it: LATIN_MARKETPLACE.it,
  ms: LATIN_MARKETPLACE.ms,
  pt: LATIN_MARKETPLACE.pt,
  ru: { ...SCRIPTS_MARKETPLACE.ru, ...SCRIPTS_ENGINE.ru },
  ur: { ...SCRIPTS_MARKETPLACE.ur, ...SCRIPTS_ENGINE.ur },
  zh: { ...SCRIPTS_MARKETPLACE.zh, ...SCRIPTS_ENGINE.zh },
};

/**
 * Read a catalogue, or return an empty shell when it is unreadable.
 *
 * Tolerating a corrupt file is deliberate and narrow. This applier rebuilds the
 * English base from `PUBLIC_PAGES`, `FIRST_BLOCK` and `META_BLOCK_ONE`, so a
 * missing or empty `en.json` is recoverable — but only if the loader does not
 * refuse to start. The old behaviour was to throw on the empty file, which left
 * the one catalogue that could be rebuilt from source as the one that could not
 * be.
 */
function load(locale) {
  const file = join(MESSAGES, `${locale}.json`);
  try {
    return JSON.parse(readFileSync(file, 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT') return {};
    if (error instanceof SyntaxError) {
      console.warn(`  ${locale}.json did not parse; rebuilding it from the source tables`);
      return {};
    }
    throw error;
  }
}

/**
 * Write a catalogue atomically, and refuse a write that would lose data.
 *
 * This applier runs its "no hand-written pair, so drop the entry" branch over
 * every locale, and for two of those runs it was pointed at `en` by mistake and
 * deleted the reference catalogue's own 305 keys. `en` is skipped now, but a
 * silent destructive transform on a hand-maintained file is the kind of thing
 * that happens twice, so two things guard it here:
 *
 *   - the previous text is kept beside the file, and
 *   - a write that would drop more than a quarter of the existing entries is
 *     treated as a mistake rather than as a translation pass, because no real
 *     translation pass removes that much at once.
 *
 * The gate that follows is the real check; this stops the damage before the gate
 * has to notice.
 */
const MIN_RETENTION = 0.75;

function writeCatalogue(locale, catalogue) {
  const file = join(MESSAGES, `${locale}.json`);
  let beforeCount = 0;
  try {
    beforeCount = Object.keys(JSON.parse(readFileSync(file, 'utf8')).pageMeta ?? {}).length;
  } catch {
    // Unreadable or absent: nothing to protect, and the source tables rebuild it.
    beforeCount = 0;
  }
  const afterCount = Object.keys(catalogue.pageMeta ?? {}).length;

  if (beforeCount > 0 && afterCount < beforeCount * MIN_RETENTION) {
    throw new Error(
      `${locale}: the pass would cut pageMeta from ${beforeCount} to ${afterCount} entries. ` +
        `That is a mistake, not a translation pass. Nothing was written; the previous ` +
        `catalogue is at ${file}.`,
    );
  }

  // A backup is kept only when the pass is about to remove something, which is
  // the only case where losing the previous text would hurt. Writing one on every
  // run leaves fourteen files in the messages tree, and a concurrent test copying
  // that tree can then read a half-written pair.
  if (beforeCount > afterCount) {
    writeFileSync(`${file}.bak`, readFileSync(file, 'utf8'), 'utf8');
  }
  writeFileSync(file, `${JSON.stringify(catalogue, null, 2)}\n`, 'utf8');
  return { beforeCount, afterCount };
}

// English is the reference, and it is spread across two sources.
const en = load('en');
en.pageMeta ??= {};

// Namespaces and keys that HEAD predates, restored so the reference catalogue is
// complete rather than merely parseable. `en` is the merge base for every locale,
// so a key missing here is a key the other twelve inherit nothing from.
for (const [namespace, value] of Object.entries(MISSING_NAMESPACES)) {
  // Merged rather than replaced: HEAD already has most of these namespaces, and
  // the working tree had grown keys inside them.
  en[namespace] = { ...(en[namespace] ?? {}), ...value };
}

/**
 * `offline.*` is written into every locale rather than the reference only.
 *
 * `ResourcePage` uses it for the offline state of all 128 generated pages, and it
 * existed only in `en` and `fa` — so a reader of `/hi/hydroma/carbon` with no
 * connection got an English sentence inside an otherwise Hindi page. No gate
 * caught it: the key *was* present in the reference catalogue, so
 * `check-message-usage` was satisfied. It was found by looking at the rendered
 * page, which is the only place a half-translated surface is visible.
 */
for (const [locale, value] of Object.entries(OFFLINE)) {
  const catalogue = load(locale);
  catalogue.offline = { ...(catalogue.offline ?? {}), ...value };
  writeCatalogue(locale, catalogue);
}

// The English base is rebuilt from four sources, in order. `PUBLIC_PAGES` and
// `FIRST_BLOCK` were recovered after `en.json` was emptied — twice by the applier
// and once by a diagnostic of mine that opened the file with the truncate flag —
// and they exist here so the reference catalogue is a build product rather than
// something hand-merged in place.
const ENGLISH_BASE = {
  ...MISSING_PAGE_META,
  ...PUBLIC_PAGES,
  ...FIRST_BLOCK,
  ...META_BLOCK_ONE,
};

for (const [slug, [title, description]] of Object.entries(ENGLISH_BASE)) {
  if (en.pageMeta[slug]) continue;
  en.pageMeta[slug] = { title, description };
}
writeCatalogue('en', en);

/**
 * Every slug the applier manages.
 *
 * Taken from `en.json` rather than from the generator's report, because that
 * report only lists the slugs still missing at the moment it ran — once the
 * applier has written them all, the report is empty and a report-driven pass
 * does nothing. Processing the whole catalogue is safe: the `kept` branch below
 * leaves any entry whose description is already not the English one, so the 53
 * hand-written public pages are untouched.
 */
const known = Object.keys(en.pageMeta);

const problems = [];
for (const slug of known) {
  const entry = en.pageMeta[slug];
  if (typeof entry.title !== 'string' || entry.title.trim() === '') problems.push(`${slug}: empty title`);
  if (typeof entry.description !== 'string' || entry.description.trim() === '') {
    problems.push(`${slug}: empty description`);
  }
}
if (problems.length > 0) {
  console.error(`refusing to write; ${problems.length} problem(s):`);
  for (const problem of problems.slice(0, 20)) console.error(`  - ${problem}`);
  process.exit(1);
}

const locales = readdirSync(MESSAGES)
  .filter((file) => file.endsWith('.json'))
  .map((file) => file.slice(0, -5));

const rows = [];

for (const locale of locales) {
  const catalogue = load(locale);
  catalogue.pageMeta ??= {};

  // English is the reference, not a participant. Running the prune branch on it
  // deleted 229 of its own keys on the previous pass, which then collapsed the
  // whole pass to the few slugs that happened to survive. It is written above and
  // never pruned.
  if (locale === 'en') {
    rows.push('  en    (reference; never pruned)');
    continue;
  }

  let full = 0;
  let inherited = 0;
  let kept = 0;

  for (const slug of known) {
    const english = en.pageMeta[slug];
    const current = catalogue.pageMeta[slug];

    if (current && current.description !== english.description) {
      kept += 1;
      continue;
    }

    const complete = FULL[locale]?.[slug];
    if (complete) {
      catalogue.pageMeta[slug] = { title: complete[0], description: complete[1] };
      full += 1;
      continue;
    }

    // No hand-written pair for this locale. The entry is *removed* rather than
    // written in English.
    //
    // Writing the English string into `zh.json` would make that catalogue claim
    // to be Chinese while holding English, which is the same lie as the original
    // mojibake: it looks translated to any structural check, including the
    // script-affinity floor, which then has to be lowered to accommodate it. The
    // runtime already merges `en` underneath every locale, so an absent entry
    // renders the English string *honestly*, and `check-page-meta` verifies the
    // effective catalogue rather than the own-key set.
    if (current) {
      delete catalogue.pageMeta[slug];
      inherited += 1;
    } else {
      inherited += 1;
    }
  }

  writeCatalogue(locale, catalogue);
  rows.push(
    `  ${locale.padEnd(4)} ${String(full).padStart(3)} complete · ${String(inherited).padStart(3)} inherited from en · ${kept} kept`,
  );
}

console.log(`pageMeta: ${known.length} slugs across ${locales.length} locales`);
console.log('per locale (complete = title+description hand-written):');
for (const row of rows) console.log(row);
