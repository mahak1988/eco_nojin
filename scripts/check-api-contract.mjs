#!/usr/bin/env node
/**
 * Contract gate (phase B3).
 *
 * Every `/api/...` path the frontend code uses must exist in the published
 * OpenAPI document. A path that is used but not published is a bind without a
 * contract — exactly the failure mode this gate exists to prevent.
 *
 * Exits 1 when at least one used path has no matching published path.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = process.cwd();
const OPENAPI = join(ROOT, 'openapi.json');
const ALLOWLIST = join(ROOT, 'docs', 'frontend', 'contract-allowlist.json');
const SCAN_DIRS = [join(ROOT, 'apps', 'web', 'src'), join(ROOT, 'packages', 'api-client', 'src')];
const SKIP = /(node_modules|\.next|\.test\.|\.spec\.|[/\\]tests[/\\])/;

/**
 * Paths owned by the Next BFF itself (not backend contracts) plus demo-only
 * endpoints used to exercise the design system.
 */
const INTERNAL = [
  /^\/api$/,
  /^\/api\/auth\//,
  /^\/api\/observability\//,
  /^\/api\/csp-report$/,
  /^\/api\/v1\/example$/,
];

// Path constants used only as prefixes (e.g. MARKETPLACE_BASE = '/api/v1/marketplace')
// are not endpoints; interpolated calls elsewhere carry the real paths.
const PREFIX_CONSTANT = /(BASE|PREFIX|ROOT|ROOT_URL|_URL)$/;
const prefixValues = new Set();

/**
 * Paths built dynamically (the first segment after /api is interpolated) cannot
 * be verified statically; they are reported separately instead of as gaps.
 */
const DYNAMIC = [/^\/api\/\{param\}/, /^\/api\/v1\/\{param\}(\/|$)/];

function walk(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (SKIP.test(full)) continue;
    if (entry.isDirectory()) walk(full, acc);
    else if (/\.(ts|tsx|mts|mjs)$/.test(entry.name)) acc.push(full);
  }
  return acc;
}

function toRegex(apiPath) {
  const normalised = apiPath.replace(/\/+$/, '') || '/';
  const escaped = normalised
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\\\{[^}]+\\\}/g, '[^/]+');
  return new RegExp(`^${escaped}$`);
}

const spec = JSON.parse(readFileSync(OPENAPI, 'utf8'));
const published = Object.keys(spec.paths || {}).map((p) => ({ raw: p, re: toRegex(p) }));

// Collect candidate usages: string literals and template literals containing /api/
const usage = new Map();
const literal = /(["'`])(\/api\/[A-Za-z0-9_\-./{}$]*)\1/g;

for (const dir of SCAN_DIRS) {
  let files = [];
  try {
    if (statSync(dir).isDirectory()) files = walk(dir);
  } catch {
    continue;
  }
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    for (const m of text.matchAll(/(?:const|let)\s+([A-Z0-9_]+)\s*=\s*(['"])(\/api\/[^'"]*)\2/g)) {
      if (PREFIX_CONSTANT.test(m[1])) prefixValues.add(m[3].replace(/\/+$/, ''));
    }
    let match;
    while ((match = literal.exec(text)) !== null) {
      const raw = match[2];
      if (raw.includes('/api/[...')) continue; // BFF catch-all route
      if (INTERNAL.some((re) => re.test(raw.replace(/\/$/, '')))) continue;
      if (prefixValues.has(raw.replace(/\/+$/, ''))) continue; // prefix constant
      const normalised = raw
        .replace(/\$\{[^}]+\}/g, '{param}')
        .replace(/\{[^}]+\}/g, '{param}')
        .replace(/\/+$/, '') || '/';
      const key = normalised;
      if (!usage.has(key)) usage.set(key, new Set());
      usage.get(key).add(relative(ROOT, file));
    }
  }
}

const missing = [];
const matched = [];
const dynamic = [];
for (const [path, files] of [...usage.entries()].sort()) {
  if (DYNAMIC.some((re) => re.test(path))) {
    dynamic.push({ path, files: [...files].sort() });
    continue;
  }
  const probe = path.replace(/\{param\}/g, 'x');
  const hit = published.some((p) => p.re.test(probe));
  if (hit) matched.push(path);
  else missing.push({ path, files: [...files].sort() });
}

// Declared content paths: static surfaces that are not API resources by design.
// A declared path must not become published; if it does, the allowlist has rotted
// and the entry must be removed (reported as a warning, not a hard failure).
let declared = [];
try {
  const allow = JSON.parse(readFileSync(ALLOWLIST, 'utf8'));
  declared = Array.isArray(allow.declaredContent) ? allow.declaredContent : [];
} catch {
  declared = [];
}
const declaredPaths = new Set(declared.map((entry) => entry.path));
const declaredUsed = [];
const undeclared = [];
for (const item of missing) {
  if (declaredPaths.has(item.path)) declaredUsed.push(item);
  else undeclared.push(item);
}
const rotted = declared
  .filter((entry) => !missing.some((item) => item.path === entry.path))
  .map((entry) => entry.path);

if (process.argv.includes('--json')) {
  process.stdout.write(
    JSON.stringify(
      {
        generatedFor: 'phase-b3 contract gate',
        publishedPaths: published.length,
        usedPaths: usage.size,
        matchedPaths: matched.length,
        dynamicPaths: dynamic.length,
        declaredContentPaths: declaredUsed.length,
        missingPaths: undeclared.length,
        allowlistRot: rotted,
        dynamic,
        declaredContent: declaredUsed,
        missing: undeclared,
      },
      null,
      2,
    ),
  );
  process.exit(undeclared.length ? 1 : 0);
}

console.log(`published paths : ${published.length}`);
console.log(`used paths      : ${usage.size}`);
console.log(`matched         : ${matched.length}`);
console.log(`dynamic (skipped): ${dynamic.length}`);
console.log(`declared content : ${declaredUsed.length}  (static surfaces, no endpoint by design)`);
console.log(`missing         : ${undeclared.length}`);
if (rotted.length) {
  console.log(`\nAllowlist rot (now published, remove from allowlist): ${rotted.join(', ')}`);
}

if (undeclared.length) {
  console.log('\nUsed but NOT published:');
  for (const item of undeclared) {
    console.log(`  ${item.path}`);
    for (const f of item.files.slice(0, 3)) console.log(`      ${f}`);
  }
  process.exit(1);
}

console.log('\nOK — every used API path is either published or declared as content.');
