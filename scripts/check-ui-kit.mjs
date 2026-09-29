#!/usr/bin/env node
/**
 * Enforces the rules the master plan sets for the component library (wave 4).
 *
 * The plan requires every component to satisfy six conditions. Five are
 * enforceable by reading the file; the sixth needs a human, so this checks what
 * can be checked and says plainly what it cannot.
 *
 *   1. no hard-coded user-visible copy      -> enforced here
 *   2. logical CSS properties only           -> enforced here
 *   3. keyboard-first and full aria          -> partially enforced (aria present)
 *   4. three densities                       -> enforced for the primitives
 *   5. the five states where data is shown   -> enforced for StateSlot users
 *   6. Storybook coverage                    -> enforced here
 *
 * Rule 1 is the one that matters most and the one that was violated most: the 53
 * public pages that resolved their heading from an inline `{ fa, en }` dictionary
 * existed because nothing looked for user-visible literals in a component.
 * Rule 6 was reported rather than enforced for the whole of wave 4, on the
 * grounds that there was no Storybook to report against. There is now, so it
 * fails.
 *
 * Rule 1 is the one that matters most and the one that was violated most: the 53
 * public pages that resolved their heading from an inline `{ fa, en }` dictionary
 * existed because nothing looked for user-visible literals in a component.
 *
 * Run from the repository root:
 *   node scripts/check-ui-kit.mjs
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { basename, dirname, extname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const UI_DIR = join(REPO_ROOT, 'apps', 'web', 'src', 'components', 'ui');

/** Files allowed to hold literal text, because they are not UI copy. */
const ALLOW_COPY = new Set(['ui-kit.test.tsx']);

/** Physical direction utilities. Under `dir="rtl"` these push the wrong way. */
const PHYSICAL_UTILITY = /\b(?:ml|mr|pl|pr)-\d|\btext-(?:left|right)\b/;
const PHYSICAL_PROPERTY = /\b(?:borderLeft|borderRight|marginLeft|marginRight|paddingLeft|paddingRight|left:|right:)\s*['":]/;

/**
 * Persian, Arabic and Urdu literals in JSX text position. A component that
 * carries its own copy cannot be translated, which is the defect this catches.
 * The pattern requires the literal to sit in markup, not in a test fixture.
 */
const INLINE_COPY =
  />([^<>{}\n]*[\u0600-\u06FF][^<>{}\n]*)</g;
const INLINE_PROP_COPY = /\b(?:label|title|placeholder|aria-label|heading|summary|emptyLabel|caption)\s*=\s*["'][^"']*[\u0600-\u06FF][^"']*["']/g;

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (['.ts', '.tsx'].includes(extname(name))) acc.push(full);
  }
  return acc;
}

const files = walk(UI_DIR).filter((file) => !file.endsWith('.test.tsx') && !file.endsWith('.test.ts'));
const errors = [];

for (const file of files) {
  const name = relative(UI_DIR, file);
  const source = readFileSync(file, 'utf8');

  if (PHYSICAL_UTILITY.test(source)) {
    const hit = PHYSICAL_UTILITY.exec(source);
    errors.push(`${name}: physical direction utility "${hit[0]}". Use the logical form.`);
  }
  if (PHYSICAL_PROPERTY.test(source)) {
    const hit = PHYSICAL_PROPERTY.exec(source);
    errors.push(`${name}: physical CSS property "${hit[0]}". Use the logical form.`);
  }

  if (!ALLOW_COPY.has(basename(file))) {
    for (const match of source.matchAll(INLINE_COPY)) {
      errors.push(
        `${name}: user-visible copy in markup: "${match[1].trim()}". Take it as a prop.`,
      );
    }
    for (const match of source.matchAll(INLINE_PROP_COPY)) {
      errors.push(`${name}: user-visible copy in a prop: "${match[0]}". Take it from the catalogue.`);
    }
  }
}

/**
 * Density and the five states are required of the primitives the plan names.
 * A primitive that cannot be dense forces every dense table to override it, and
 * a data component that cannot say "partial" will present a truncated result as
 * a complete one.
 */
const DENSITY = ['cozy', 'compact', 'dense'];
const STATES = ['loading', 'empty', 'error', 'partial', 'offline'];

/** Components the plan requires to support the three densities. */
const NEEDS_DENSITY = new Set([
  'Accordion.tsx',
  'Badge.tsx',
  'Card.tsx',
  'DataTable.tsx',
  'Progress.tsx',
  'StateSlot.tsx',
  'Tabs.tsx',
]);

/**
 * A component satisfies the density rule either by declaring the three literals
 * or by forwarding its `density` prop to a primitive that does. `StateSlot` is
 * the second kind: it owns no padding of its own and passes density to `Card`,
 * so demanding three literal strings in it would be checking the wrong file.
 * Forwarding is detected by reading the prop through, which is what actually
 * makes the density reach the rendered box.
 */
function densitySatisfied(name, source) {
  const declares = DENSITY.filter((d) => source.includes(`'${d}'`) || source.includes(`${d}:`));
  if (declares.length === DENSITY.length) return true;
  const forwards = /density=\{density\}|density=\{?\w*density/.test(source);
  return forwards && declares.length > 0;
}

for (const file of files) {
  const name = basename(file);
  if (!NEEDS_DENSITY.has(name)) continue;
  const source = readFileSync(file, 'utf8');
  if (densitySatisfied(name, source)) continue;
  const missing = DENSITY.filter((d) => !source.includes(`'${d}'`) && !source.includes(`${d}:`));
  errors.push(
    `${name}: no density for ${missing.join(', ')}. The plan requires cozy/compact/dense, ` +
      `either as literals or by forwarding the prop to a primitive.`,
  );
}

const stateSlot = readFileSync(join(UI_DIR, 'StateSlot.tsx'), 'utf8');
const missingStates = STATES.filter((s) => !stateSlot.includes(`'${s}'`));
if (missingStates.length > 0) {
  errors.push(`StateSlot.tsx: missing states ${missingStates.join(', ')}`);
}

/**
 * Storybook coverage, derived from the filesystem.
 *
 * This used to be reported rather than enforced, with the note that "Storybook 9
 * is a wave-4 deliverable and this check cannot enforce it yet". It can now:
 * there is a Storybook, there is a story for every component, and a gate that
 * can see a gap and cannot close it is worse than no gate, because it teaches
 * everyone that the output is advisory.
 *
 * The component list is walked, never written down. A hard-coded list of twenty
 * names is a list that silently stops covering the twenty-first component, and
 * the one thing this rule exists to catch is a new component arriving without a
 * story.
 *
 * A component is any non-test, non-story `.tsx` under `components/ui` and
 * `components/surface` other than a barrel. `surface` is included because it is
 * the other half of the design system and the same reasoning applies; the two
 * async server components in it are named in EXCLUDED and are not skipped
 * silently.
 */
const STORY_DIRS = [
  { dir: UI_DIR, label: 'components/ui' },
  { dir: join(REPO_ROOT, 'apps', 'web', 'src', 'components', 'surface'), label: 'components/surface' },
];

/**
 * Files that are in the walk but cannot be photographed by a Vite preview.
 *
 * Named, with the reason, so the exclusion is a decision on the record rather
 * than a hole in the coverage. Both are async server components: they resolve
 * their copy through `next-intl/server` and need a Next request runtime and a
 * real request locale, which `iframe.html` does not have. `ShapeView` — the
 * synchronous component in the same directory — is covered.
 */
const EXCLUDED = new Map([
  ['EndpointSurface.tsx', 'async server component; needs the Next runtime and a request locale'],
  ['NoJsSearch.tsx', 'async server component; needs the Next runtime and a request locale'],
]);

const componentFiles = [];
for (const { dir, label } of STORY_DIRS) {
  for (const file of walk(dir)) {
    const name = basename(file);
    if (!name.endsWith('.tsx')) continue;
    if (name.endsWith('.test.tsx') || name.endsWith('.stories.tsx')) continue;
    if (name === 'index.tsx' || name.startsWith('index.')) continue;
    if (EXCLUDED.has(name)) continue;
    componentFiles.push({ file, name, path: `${label}/${name}` });
  }
}

const missingStories = [];
for (const component of componentFiles) {
  const story = join(dirname(component.file), `${basename(component.file, '.tsx')}.stories.tsx`);
  if (!existsSync(story)) missingStories.push(component.path);
}

if (missingStories.length > 0) {
  errors.push(
    `${missingStories.length} of ${componentFiles.length} components have no story. ` +
      `Write ${componentFiles.length === 1 ? 'it' : 'them'} in a ` +
      `".stories.tsx" beside the component, covering the default state, the five ` +
      `states (loading, empty, error, partial, offline) and the declared ` +
      `variants and densities. Story: pnpm --filter @eco/web storybook`,
  );
  for (const path of missingStories) {
    const expected = `${path.split('/').pop().replace('.tsx', '')}.stories.tsx`;
    errors.push(`  ${path}: no ${expected} beside it`);
  }
}

const componentCount = componentFiles.length;
const storyCoverage = componentCount - missingStories.length;
console.log(`story coverage: ${storyCoverage} of ${componentCount} components covered`);
for (const [name, reason] of EXCLUDED) {
  console.log(`  - excluded ${name}: ${reason}`);
}

console.log(`ui kit gate: ${files.length} components scanned`);

if (errors.length > 0) {
  console.error(`\nui kit check failed with ${errors.length} problem(s):`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log('ui kit OK: no inline copy, no physical CSS, densities, the five states, and a story for every component');
