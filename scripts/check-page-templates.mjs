#!/usr/bin/env node
/**
 * Fails the build when a catalogue route has no page template, has two, or when
 * a template's declaration has lost one of the properties the master plan makes
 * non-negotiable.
 *
 * The design layer already proves these rules in TypeScript — a template cannot
 * drop `partial` from its five states or name a different region for the source
 * stamp without failing to compile. This gate exists for the things the type
 * system cannot see from inside a single file:
 *
 *   1. PARTITION.  `PAGE_TEMPLATES` is a *partition* of the catalogue, not a
 *      suggestion list. A route that matches no template, or two, is a routing
 *      design problem and it is reported by path so it can be fixed.
 *   2. COVERAGE.  Every one of the twelve claims at least one real route, so a
 *      template cannot rot into dead code that still looks load-bearing.
 *   3. RENDER.    Every template's declared regions actually render, with the
 *      five states and the stamp on the anchor region. The plan's rule that a
 *      page shows exactly one of five states is a rendering rule, not a
 *      declaration rule.
 * 4. LOGICAL.   The template sources use no physical CSS property. The platform
 *      is RTL-first, and `check-ui-kit.mjs` only scans `src/components/ui/`, so
 *      this is the gate that reads these files.
 *
 * Colour utilities are deliberately NOT re-checked here: `check-colour-utilities.mjs`
 * already walks all of `apps/web/src` and resolves every colour utility against
 * the theme block in `globals.css`, these files included. A second, weaker copy
 * would only produce disagreements about what a class run is.
 *
 * Usage:
 *   node scripts/check-page-templates.mjs [--quiet] [--json]
 *
 * Exits 0 when clean, 1 on any failure. `--quiet` prints only the per-template
 * counts; `--json` prints the full report for a CI artefact.
 */

import { spawnSync } from 'node:child_process';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..');
const WEB = path.join(REPO, 'apps', 'web');

/**
 * The two modules this gate reads are TypeScript, and Node only strips types
 * behind a flag. Re-exec once with the flag rather than transpiling by hand: a
 * hand-rolled stripper is how a gate ends up silently testing a mangled copy of
 * the source, which is worse than not having a gate.
 */
if (!process.env.PAGE_TEMPLATE_GATE_TS) {
  const child = spawnSync(
    process.execPath,
    ['--experimental-strip-types', '--no-warnings', fileURLToPath(import.meta.url), ...process.argv.slice(2)],
    { stdio: 'inherit', env: { ...process.env, PAGE_TEMPLATE_GATE_TS: '1' } },
  );
  process.exit(child.status ?? 1);
}

const argv = new Set(process.argv.slice(2));
const QUIET = argv.has('--quiet');
const AS_JSON = argv.has('--json');

const fail = [];
const failLines = [];

function report(group, lines) {
  fail.push(group);
  for (const line of lines) failLines.push(`  [${group}] ${line}`);
}

/* ------------------------------------------------------------------ *
 * 1 + 2. The partition, over the real catalogue.
 * ------------------------------------------------------------------ */

const { PAGE_CATALOG } = await import(
  pathToFileURL(path.join(WEB, 'src', 'lib', 'domains', 'page-catalog.ts')).href
);

const {
  PAGE_TEMPLATES,
  PAGE_TEMPLATE_COUNT,
  REQUIRED_STATES,
  MANDATORY_REGIONS,
  TEMPLATE_IDS,
  createRouteContext,
  matchTemplates,
  templateCoverage,
} = await import(
  pathToFileURL(path.join(WEB, 'src', 'lib', 'design', 'page-templates.ts')).href
);

if (PAGE_TEMPLATES.length !== PAGE_TEMPLATE_COUNT) {
  report(
    'definition',
    [`expected ${PAGE_TEMPLATE_COUNT} templates, found ${PAGE_TEMPLATES.length}`],
  );
}

const coverage = templateCoverage(PAGE_CATALOG);

if (coverage.unmatched.length > 0) {
  report(
    'unmatched',
    coverage.unmatched.map((entry) => `${entry} — no page template claims this route`),
  );
}

if (coverage.ambiguous.length > 0) {
  report(
    'ambiguous',
    coverage.ambiguous.map(
      (entry) =>
        `${entry.path} — claimed by ${entry.templates.join(' and ')}; the layout would be decided by declaration order`,
    ),
  );
}

const total = Object.values(coverage.counts).reduce((sum, count) => sum + count, 0);
if (total + coverage.unmatched.length + coverage.ambiguous.length !== PAGE_CATALOG.length) {
  report('partition', [
    `${total} assigned, ${coverage.unmatched.length} unmatched, ${coverage.ambiguous.length} ambiguous, but the catalogue has ${PAGE_CATALOG.length} entries`,
  ]);
}

for (const id of TEMPLATE_IDS) {
  if ((coverage.counts[id] ?? 0) === 0) {
    report('coverage', [`${id} claims no catalogue entry and is dead weight`]);
  }
}

for (const template of PAGE_TEMPLATES) {
  const states = [...(template.states ?? [])];
  if (states.length !== REQUIRED_STATES.length || REQUIRED_STATES.some((s) => !states.includes(s))) {
    report('states', [
      `${template.plan}/${template.id} declares [${states.join(', ')}], not the five of §4.5`,
    ]);
  }
  for (const region of MANDATORY_REGIONS) {
    if (!template.regions.includes(region)) {
      report('regions', [`${template.plan}/${template.id} omits the mandatory region "${region}"`]);
    }
  }
  if (template.provenance?.region !== 'provenance' || template.provenance?.required !== true) {
    report('provenance', [
      `${template.plan}/${template.id} does not require the provenance region`,
    ]);
  }
  if (!template.regions.includes(template.provenance?.anchor)) {
    report('provenance', [
      `${template.plan}/${template.id} anchors the stamp to "${template.provenance?.anchor}", a region it does not render`,
    ]);
  }
}

/* ------------------------------------------------------------------ *
 * 3. Render.  Every archetype, every state, and the stamp in place.
 * ------------------------------------------------------------------ */

const TEMPLATE_DIR = path.join(WEB, 'src', 'components', 'templates');
const allFiles = readdirSync(TEMPLATE_DIR);
const FRAME = 'TemplateFrame.tsx';
const templateFiles = allFiles.filter(
  (name) => name.endsWith('.tsx') && !name.includes('.test.') && name !== FRAME && name !== 'templateTestHarness.tsx',
);

if (templateFiles.length !== PAGE_TEMPLATE_COUNT) {
  report('render', [
    `expected ${PAGE_TEMPLATE_COUNT} template components, found ${templateFiles.length}: ${templateFiles.join(', ')}`,
  ]);
}

/**
 * The invariants split in two, because the code does.
 *
 * `TemplateFrame` owns everything the plan makes non-negotiable — the five
 * states, the stamp's declared home, the regions, the landmarks and the heading
 * — so those are checked there once. Each template owns exactly two things: it
 * names the archetype it renders, and it is not a client island. Checking a
 * template for `<StateSlot` would only prove the template had stopped delegating,
 * which is the opposite of the intent.
 */
const FRAME_CHECKS = [
  { re: /data-page-template=\{template\.plan\}/, why: 'no data-page-template, so the gate and the tests cannot read the archetype' },
  { re: /data-region=\{region\}/, why: 'no data-region, so a missing region is invisible in the DOM' },
  { re: /data-provenance-region=\{anchor\}/, why: 'no data-provenance-region, so the stamp has no declared home' },
  { re: /<StateSlot\b/, why: 'does not render StateSlot, so the five states of §4.5 are not reachable' },
  { re: /state === 'ready'|state !== 'ready'/, why: 'never inspects the state, so the state slot would be unconditional' },
  { re: /id="main"/, why: 'no #main landmark, so the skip link has no target' },
  { re: /<h1\b/, why: 'renders no h1' },
  { re: /aria-labelledby/, why: 'renders regions with no accessible name' },
];

const frameSource = readFileSync(path.join(TEMPLATE_DIR, FRAME), 'utf8');
for (const check of FRAME_CHECKS) {
  if (!check.re.test(frameSource)) report('render', [`${FRAME} ${check.why}`]);
}

for (const name of [...templateFiles, FRAME]) {
  const source = readFileSync(path.join(TEMPLATE_DIR, name), 'utf8');
  if (/^\s*['"]use client['"]/m.test(source)) {
    report('render', [`${name} is a client island; a layout must stay a server component`]);
  }
  if (name === FRAME) continue;
  if (!/TEMPLATE_BY_ID\.[a-z]+/.test(source)) {
    report('render', [`${name} does not name the archetype it renders`]);
  }
  if (!/<TemplateFrame\b/.test(source)) {
    report('render', [`${name} does not render the shared frame, so it has no states and no stamp`]);
  }
}

/* ------------------------------------------------------------------ *
 * 4. Logical properties and declared colour tokens.
 * ------------------------------------------------------------------ */

const PHYSICAL = [
  { re: /(^|[\s"'`:])(ml|mr|pl|pr)-[a-z0-9./[]/, why: 'physical margin/padding; use ms-/me-/ps-/pe-' },
  { re: /(^|[\s"'`:])(left|right)-[a-z0-9./[]/, why: 'physical offset; use start-/end-' },
  { re: /text-(left|right)\b/, why: 'physical text alignment; use text-start/text-end' },
  { re: /(^|[\s"'`:])border-[lr](?![a-z0-9])/, why: 'physical border side; use border-s/border-e' },
  { re: /\b(margin|padding|border)(Left|Right)\s*:/, why: 'physical inline spacing in a style object' },
  { re: /^\s*(left|right|marginLeft|marginRight|paddingLeft|paddingRight|borderLeft|borderRight)\s*:/m, why: 'physical CSS property' },
];

for (const name of [...templateFiles, FRAME, 'index.ts']) {
  const source = readFileSync(path.join(TEMPLATE_DIR, name), 'utf8');
  for (const rule of PHYSICAL) {
    if (rule.re.test(source)) report('rtl', [`${name} uses a physical property: ${rule.why}`]);
  }
}

/* ------------------------------------------------------------------ *
 * Report
 * ------------------------------------------------------------------ */

const table = TEMPLATE_IDS.map((id) => {
  const template = PAGE_TEMPLATES.find((t) => t.id === id);
  return {
    id,
    plan: template?.plan ?? '??',
    name: template?.name ?? '??',
    density: template?.density ?? '??',
    count: coverage.counts[id] ?? 0,
  };
}).sort((a, b) => b.count - a.count);

if (AS_JSON) {
  console.log(
    JSON.stringify(
      { ok: fail.length === 0, counts: coverage.counts, table, failures: fail, details: failLines },
      null,
      2,
    ),
  );
  process.exit(fail.length === 0 ? 0 : 1);
}

if (!QUIET) {
  console.log('page templates (§4.4) over the real catalogue\n');
  const width = Math.max(...table.map((row) => row.name.length));
  for (const row of table) {
    console.log(
      `  ${row.plan}  ${row.id.padEnd(10)} ${row.name.padEnd(width)}  ${row.density.padEnd(12)} ${String(row.count).padStart(4)}`,
    );
  }
  const assigned = table.reduce((sum, row) => sum + row.count, 0);
  console.log(`\n  ${table.length} templates · ${assigned} of ${PAGE_CATALOG.length} routes assigned`);
}

if (fail.length > 0) {
  console.error(`\npage-template gate failed (${fail.length} groups):\n`);
  for (const line of failLines) console.error(line);
  console.error('');
  process.exit(1);
}

if (!QUIET) console.log('\n  every route has exactly one archetype; all five states and the stamp are rendered\n');
process.exit(0);
