import { readFileSync, readdirSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Fails when a component exports a name that nothing imports.
 *
 * Three components were written, translated to RTL correctly, and then never
 * mounted: `BazaarEstablishmentWizard`, `MarketMap` and `BazaarStepRenderer`. Two
 * of them had a route built specifically for them — `/market/bazaars/[id]/map`
 * and ten `/market/bazaars/[id]/wizard/step*` pages — which delegated to a
 * generic template instead. Nothing reported that, because nothing checked.
 *
 * A file that only exports constants or types is exempt: a route-module or a
 * token reader is not a component, and requiring it to be imported would be
 * wrong. Only files exporting a function or a component-shaped binding are
 * considered.
 *
 * `src/components/ui/` is also exempt. That directory is a component library, and
 * a library legitimately exports primitives that no page uses yet — `Toast`,
 * `Dialog`, `Switch` have no call site today and that is not a defect. The check
 * is about *feature* components, where an unmounted renderer means a page exists
 * that delegates to a generic template instead of the one written for it.
 */
const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB = join(REPO_ROOT, 'apps', 'web');
const COMPONENTS = join(WEB, 'src', 'components');
const SRC = join(WEB, 'src');

function walk(dir, acc = []) {
  for (const item of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, item.name);
    if (item.isDirectory()) walk(full, acc);
    else if (/\.tsx?$/.test(item.name)) acc.push(full);
  }
  return acc;
}

const files = walk(SRC);

/**
 * Every name another file imports, keyed by file, with the imported text already
 * collapsed to single spaces so one pattern matches a multi-line import.
 */
const importsByFile = new Map();
for (const file of files) {
  importsByFile.set(file, readFileSync(file, 'utf8').replace(/\s+/g, ' '));
}

/** Names a file exports as a function, component or component-shaped binding. */
const exportedComponents = (text) =>
  [
    ...new Set(
      [
        ...text.matchAll(/^export (?:async )?function (\w+)/gm),
        ...text.matchAll(/^export (?:const|let) (\w+)\s*[:=]\s*(?:React\.)?(?:FC|Function|forwardRef|memo)/gm),
        ...text.matchAll(/^export (?:const|let) (\w+)\s*[:=]\s*(?:async )?function/gm),
      ].map((m) => m[1]),
    ),
  ];

const UI = join(COMPONENTS, 'ui');

const componentFiles = files.filter(
  (file) =>
    file.startsWith(COMPONENTS) &&
    !file.startsWith(UI) &&
    !/\.test\.tsx?$/.test(file) &&
    basename(file) !== 'index.ts',
);

const unmountedLibrary = files
  .filter(
    (file) =>
      file.startsWith(UI) && !/\.test\.tsx?$/.test(file) && basename(file) !== 'index.ts',
  )
  .filter((file) => {
    const text = readFileSync(file, 'utf8');
    const names = exportedComponents(text);
    if (names.length === 0) return false;
    return names.every(
      (name) =>
        ![...importsByFile].some(
          ([other, imports]) => other !== file && new RegExp(`import[^;]*\\b${name}\\b[^;]*from '[^']*'`).test(imports),
        ),
    );
  })
  .map((file) => basename(file));

/**
 * A real use of `name`, whether the import is static or dynamic.
 *
 * Both forms count. A static import is `import { Name } from '…'`; a dynamic one
 * is `const { Name } = await import('…')`. Matching only the static form reports
 * a mounted component as an orphan, which is how a false positive would train
 * people to ignore this gate.
 */
const importsName = (imports, name) =>
  new RegExp(`import\\s*\\{[^}]*\\b${name}\\b[^}]*\\}\\s*from`).test(imports) ||
  new RegExp(`\\{[^}]*\\b${name}\\b[^}]*\\}\\s*=\\s*await\\s+import\\(`).test(imports) ||
  new RegExp(`import\\s+\\w+\\s*=\\s*require\\([^)]*\\)[^;]*\\b${name}\\b`).test(imports);

const problems = [];
const mounted = [];

for (const component of componentFiles) {
  const text = readFileSync(component, 'utf8');
  const names = exportedComponents(text);
  if (names.length === 0) continue;

  const used = new Set();
  for (const [file, imports] of importsByFile) {
    if (file === component) continue;
    for (const name of names) {
      // A real use is an import of that name, static or dynamic, whatever the
      // module path.
      if (importsName(imports, name)) used.add(name);
    }
  }

  const unused = names.filter((name) => !used.has(name));
  if (unused.length === 0) {
    mounted.push(relative(WEB, component));
  } else {
    problems.push(`${relative(WEB, component)} exports ${unused.join(', ')} and nothing imports it.`);
  }
}

console.log(`orphan check: ${componentFiles.length} feature component(s) scanned, all mounted`);
console.log(
  `component library: ${unmountedLibrary.length} primitive(s) exported but not yet used by a page — ` +
    `expected for a library: ${unmountedLibrary.slice(0, 6).join(', ')}${unmountedLibrary.length > 6 ? ', …' : ''}`,
);

if (problems.length > 0) {
  console.error(`\n${problems.length} feature component(s) with unmounted exports:`);
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}

console.log('no orphans: every feature component is imported somewhere');
