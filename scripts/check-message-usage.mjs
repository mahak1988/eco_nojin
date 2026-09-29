#!/usr/bin/env node
/**
 * Fails when a page asks for a message key no catalogue can resolve.
 *
 * `i18n-check.mjs` compares the locale files with each other, so it stays green
 * when the code and the catalogues disagree â€” the files agree, and both are
 * missing what a page renders. A page in that state throws `MISSING_MESSAGE` at
 * request time, the error boundary swallows it, and the route answers HTTP 200
 * with an empty body. That is a silent, shipping failure, so this check exists.
 *
 * The binding is positional: a file may rebind the same accessor name in a
 * narrower scope (`const t = await getTranslations('science')` and later
 * `const t = await getTranslations()`), so the namespace in effect at a call
 * site is the last declaration that precedes it.
 *
 * The reference catalog is `en`, because that is what `src/lib/i18n/messages.ts`
 * falls back to. Using `fa` here, while the runtime merges `en` first, meant a
 * key present in `en` but absent from `fa` rendered fine and was never checked,
 * while a key present in `fa` but absent from `en` was checked but unreachable.
 * `i18n-check.mjs` and `check-locale-depth.mjs` now agree on the same reference.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

// The gate runs both as `pnpm check:messages` from the repository root and as
// part of `pnpm -C apps/web quality`, so the root is resolved from this file
// rather than from the working directory.
const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const APP_ROOT = join(REPO_ROOT, 'apps', 'web', 'src');
const MESSAGES = join(REPO_ROOT, 'apps', 'web', 'messages');
const REFERENCE = 'en';

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (/\.tsx?$/.test(name)) acc.push(full);
  }
  return acc;
}

function loadCatalog(locale) {
  return JSON.parse(readFileSync(join(MESSAGES, `${locale}.json`), 'utf8'));
}

function has(catalog, dotted) {
  let node = catalog;
  for (const part of dotted.split('.')) {
    if (node === null || typeof node !== 'object' || !(part in node)) return false;
    node = node[part];
  }
  return true;
}

const reference = loadCatalog(REFERENCE);
const otherLocales = readdirSync(MESSAGES)
  .filter((name) => name.endsWith('.json') && name !== `${REFERENCE}.json`)
  .map((name) => [name.replace('.json', ''), loadCatalog(name.replace('.json', ''))]);

const gaps = [];
let inspectedFiles = 0;

for (const file of walk(APP_ROOT)) {
  const src = readFileSync(file, 'utf8');
  const bindings = [];
  const bindRe =
    /(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:await\s*)?(?:getTranslations|useTranslations)\(\s*(?:\{[^}]*namespace:\s*)?(?:'([^']+)'|(\)))/g;
  let bind;
  while ((bind = bindRe.exec(src))) {
    bindings.push({ name: bind[1], namespace: bind[2] ?? '', at: bind.index });
  }
  if (bindings.length === 0) continue;
  inspectedFiles += 1;

  const callRe = /\b([A-Za-z_$][\w$]*)\s*(?:\.\s*(?:raw|has)\s*)?\(\s*'([^']+)'/g;
  let call;
  while ((call = callRe.exec(src))) {
    const inScope = bindings.filter((b) => b.name === call[1] && b.at < call.index);
    if (inScope.length === 0) continue;
    const { namespace } = inScope[inScope.length - 1];
    const key = call[2];
    if (key.startsWith('/') || key.includes(' ')) continue;
    const path = namespace ? `${namespace}.${key}` : key;
    if (has(reference, path)) continue;
    gaps.push({
      path,
      where: relative(REPO_ROOT, file).split('\\').join('/'),
      resolvableElsewhere: otherLocales
        .filter(([, catalog]) => has(catalog, path))
        .map(([locale]) => locale),
    });
  }
}

const unique = new Map();
for (const gap of gaps) if (!unique.has(gap.path)) unique.set(gap.path, gap);

if (unique.size > 0) {
  console.error(`\nunresolvable message keys: ${unique.size}\n`);
  for (const gap of [...unique.values()].sort((a, b) => a.path.localeCompare(b.path))) {
    const elsewhere =
      gap.resolvableElsewhere.length > 0
        ? ` (resolvable in: ${gap.resolvableElsewhere.join(', ')})`
        : ' (missing from every locale)';
    console.error(`  ${gap.path}${elsewhere}\n      ${gap.where}`);
  }
  console.error(
    `\nA page that asks for one of these throws MISSING_MESSAGE at request time and` +
      `\nanswers HTTP 200 with an empty body. Add the key to apps/web/messages/${REFERENCE}.json.\n`,
  );
  process.exit(1);
}

console.log(
  `message usage OK: ${inspectedFiles} files, every key resolvable in ${REFERENCE}.json`,
);
