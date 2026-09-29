/**
 * Reports `var(--x)` references that resolve to nothing.
 *
 * A custom property that is never declared is not a warning. `var(--x)` with no
 * fallback is invalid at computed-value time, so the declaration it appears in is
 * dropped and the property falls back to its initial value. This was the single
 * largest silent defect the audit found: the whole UI kit set its metrics
 * through `var(--space-1..8)`, `var(--radius-2/8/16)` and `var(--color-muted)`,
 * and `globals.css` declared none of them, so `Button`, `Card`, `Dialog`,
 * `DataTable`, `Accordion`, `Badge`, `CommandPalette`, `Skeleton`, `StateSlot`
 * and `Toast` all rendered with no padding, no gap and square corners while
 * reading as though they were styled. Nothing else in the suite could see it:
 * the references are valid TypeScript and valid CSS.
 *
 * Declarations are collected from the stylesheet *and* from the components, so a
 * token a component sets on its own element (`style={{ '--accent': x }}`) is not
 * reported as undefined.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const WEB = join(dirname(dirname(fileURLToPath(import.meta.url))), 'apps', 'web');

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (/\.(tsx|ts|css)$/.test(name)) acc.push(full);
  }
  return acc;
}

const files = walk(join(WEB, 'src'));
const css = readFileSync(join(WEB, 'src', 'app', 'globals.css'), 'utf8');

/** Declared in the stylesheet, or set inline by the component that reads it. */
const declared = new Set();
for (const file of files) {
  // The quotes matter: a component-scoped token is written as an object key,
  // `style={{ '--accent': value }}`, so the name is followed by `':` and not by
  // a bare colon.
  for (const match of readFileSync(file, 'utf8').matchAll(/['"`]?(--[a-z0-9-]+)['"`]?\s*:/g)) {
    declared.add(match[1]);
  }
}
/** Every custom property the stylesheet itself declares. */
const references = new Map();
for (const file of files) {
  const source = readFileSync(file, 'utf8');
  for (const match of source.matchAll(/var\(\s*(--[a-z0-9-]+)\s*([,)])/g)) {
    const [, name, terminator] = match;
    // A fallback argument means the author already knew it might be absent.
    if (terminator === ',') continue;
    if (declared.has(name)) continue;
    if (!references.has(name)) references.set(name, new Set());
    references.get(name).add(relative(WEB, file));
  }
}

console.log(`${declared.size} custom properties declared across the stylesheet and components`);
if (references.size === 0) {
  console.log('every var(--x) reference without a fallback resolves');
  process.exit(0);
}
console.log(`\n${references.size} reference(s) with no fallback and no declaration:`);
for (const [name, used] of [...references].sort((a, b) => b[1].size - a[1].size)) {
  console.log(`  ${name}  (${used.size} file(s))`);
  for (const file of [...used].slice(0, 5)) console.log(`      ${file}`);
  if (used.size > 5) console.log(`      ... and ${used.size - 5} more`);
}
console.error(
  '\nA `var(--x)` with no fallback and no declaration is invalid at computed-value time, so the\n' +
    'declaration it appears in is dropped and the property falls back to its initial value.',
);
process.exit(1);
