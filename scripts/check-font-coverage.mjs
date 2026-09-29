#!/usr/bin/env node
/**
 * Reports which of the fourteen official locales have a bundled font covering
 * their script, and fails when a locale is added with no way to render it.
 *
 * Why this is a gate and not a note
 * ---------------------------------
 * `globals.css` bundles three families: Vazirmatn and Markazi Text (Arabic) and
 * JetBrains Mono (Latin). Six locales are covered by those. The remaining four
 * write in scripts none of them reaches — Devanagari (`hi`), Bengali (`bn`),
 * CJK (`zh`) and Nastaliq (`ur`) — and were falling through to whatever
 * `ui-sans-serif` the reader's OS supplied, with no control over weight, line
 * height or digit form.
 *
 * The CSS now names a deliberate family per script (see `--font-sans-deva` and
 * friends), which resolves against fonts the reader already has and therefore
 * costs no bundle weight. That is mitigation, not a fix: the exact face is still
 * the reader's. Bundling Noto Sans Devanagari, Noto Sans Bengali, Noto Sans SC
 * and Noto Nastaliq UI is R-13 in FRONTEND_COMPLETION_PLAN_FA_2026-09-26.md.
 *
 * So this gate does two things: it prints the real coverage so the gap cannot be
 * forgotten, and it hard-fails on a locale with neither a bundled font nor a
 * declared script stack, which is a regression rather than a known limitation.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB = join(REPO_ROOT, 'apps', 'web');
/** Overridable so the gate can be run against a doctored stylesheet in a test. */
const CSS = process.env.ECO_CSS_FILE ?? join(WEB, 'src', 'app', 'globals.css');

/** Which script each bundled family actually carries. */
const BUNDLED_SCRIPT = {
  Vazirmatn: 'Arabic',
  'Markazi Text': 'Arabic',
  'JetBrains Mono': 'Latin',
};

/** Locales that need a script the bundle does not carry, and the stack that covers it. */
const SCRIPT_STACKS = {
  hi: { stack: '--font-sans-deva', script: 'Devanagari' },
  bn: { stack: '--font-sans-beng', script: 'Bengali' },
  zh: { stack: '--font-sans-cjk', script: 'CJK' },
  ur: { stack: '--font-sans-nastaliq', script: 'Nastaliq' },
};

/** Locales served by a bundled family, with the family that covers them. */
const BUNDLED_LOCALES = {
  fa: 'Vazirmatn',
  en: 'JetBrains Mono',
  ar: 'Vazirmatn',
  de: 'JetBrains Mono',
  es: 'JetBrains Mono',
  fr: 'JetBrains Mono',
  it: 'JetBrains Mono',
  ms: 'JetBrains Mono',
  pt: 'JetBrains Mono',
  ru: 'JetBrains Mono',
};

const css = readFileSync(CSS, 'utf8');

const bundledFamilies = new Set(
  [...css.matchAll(/font-family:\s*"([^"]+)";/g)].map((match) => match[1]),
).intersection(new Set(Object.keys(BUNDLED_SCRIPT)));

const errors = [];
const rows = [];

// 1. Every locale must be served by a bundled family or a declared script stack.
for (const [locale, family] of Object.entries(BUNDLED_LOCALES)) {
  if (!bundledFamilies.has(family)) {
    errors.push(
      `${locale} is assigned the bundled family "${family}", but no @font-face in globals.css declares it`,
    );
    continue;
  }
  rows.push(`  ${locale.padEnd(4)} bundled       ${family} (${BUNDLED_SCRIPT[family]})`);
}

for (const [locale, info] of Object.entries(SCRIPT_STACKS)) {
  const declared = css.includes(`${info.stack}:`);
  if (!declared) {
    errors.push(
      `${locale} needs the ${info.script} script and no --font-sans-* stack is declared for it. ` +
        `Add one, or bundle a font.`,
    );
  }
  rows.push(
    `  ${locale.padEnd(4)} ${declared ? 'script stack' : 'MISSING     '} ${info.script} (${info.stack})`,
  );
}

// 2. Every script stack must actually resolve to a named family, not just the
//    generic fallback, or it is a rename of the problem.
for (const [locale, info] of Object.entries(SCRIPT_STACKS)) {
  const declaration = new RegExp(`${info.stack}:([^;]+);`).exec(css);
  if (!declaration) continue;
  const value = declaration[1];
  if (/^var\(--font-sans\)$/.test(value.trim())) {
    errors.push(`${locale}: ${info.stack} resolves straight to --font-sans, so nothing changes`);
  }
  if (value.includes('local(')) {
    errors.push(
      `${locale}: ${info.stack} uses a local() src, which no @font-face here defines. ` +
        `Use a family name so the reader's installed font is picked up.`,
    );
  }
}

// 3. The per-locale selectors must exist, or the stack is declared and unused.
//    The attribute selector is matched with a tolerant quote pattern: Biome
//    normalises `html[lang='hi']` to `html[lang="hi"]`, so a single-quoted search
//    would report every one of these as missing.
for (const locale of Object.keys(SCRIPT_STACKS)) {
  const selector = new RegExp(`html\\[lang=['"]${locale}['"]\\]`);
  if (!selector.test(css)) {
    errors.push(
      `${locale} has a font stack but no html[lang] rule, so the stack is never applied`,
    );
  }
}

console.log(
  `font coverage: ${bundledFamilies.size} bundled families, ${Object.keys(SCRIPT_STACKS).length} script stacks`,
);
for (const row of rows) console.log(row);

if (errors.length > 0) {
  console.error(`\nfont coverage check failed with ${errors.length} problem(s):`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log(
  '\nfont coverage OK: every locale resolves to a named family. ' +
    'Four scripts are still served by the reader\u2019s installed font rather than a bundled one (R-13).',
);
