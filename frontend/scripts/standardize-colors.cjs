/**
 * Color standardization script for Eco Nojin frontend.
 * Replaces Tailwind shorthand color classes with CSS variable equivalents.
 *
 * Scope:
 * - emerald shades are remapped to the custom palette (night + leaf)
 * - leaf, night, sand, aqua shorthands become var(--color-...)
 *
 * Run: node scripts/standardize-colors.cjs
 * Test: npx tsc --noEmit && npx eslint . && npx vitest run
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ── Emerald shade → target palette (CSS variable name without -- prefix) ──
const EMERALD_MAP = {
  50:  'night-100',
  100: 'night-200',
  300: 'leaf-300',
  400: 'leaf-400',
  500: 'leaf-500',
  900: 'night-800',
};

// ── Custom palette names that map 1:1 to CSS variables ──
const CUSTOM_PALETTES = ['leaf', 'night', 'sand', 'aqua'];

// ── Shade numbers we support (2-3 digits, matching design tokens) ──
// Non-capturing group — the outer regex adds the capturing group
const SHADES_RE = '(?:50|100|200|300|400|500|600|700|800|900|950)';

// ── Property types that carry a color value ──
//   text, bg, border, ring, fill, stroke
const PROP_RE = '(text|bg|border|ring|fill|stroke)';

// ── Variant prefixes that may precede a class ──
//   hover:, focus:, focus-within:, active:, group-hover:, file:, placeholder:, etc.
const VARIANT_RE = '([a-z-]+:)?';

// ── Match an emerald color class ──
//   e.g. text-emerald-50, hover:bg-emerald-400/10, placeholder:text-emerald-100/30
const EMERALD_RE = new RegExp(
  `${VARIANT_RE}${PROP_RE}-emerald-(${SHADES_RE})(?:\\/(\\d+))?(?![0-9])`,
  'g',
);

// ── Match a custom-palette color class ──
const CUSTOM_RE = new RegExp(
  `${VARIANT_RE}${PROP_RE}-(${CUSTOM_PALETTES.join('|')})-(${SHADES_RE})(?:\\/(\\d+))?(?![0-9])`,
  'g',
);

function buildVar(className, shade, opacity) {
  // shade is the palette name (e.g. "leaf", "night"), opacity is the /NN value
  const colorVar = `--color-${className}-${shade}`;
  return `var(${colorVar})` + (opacity ? `/${opacity}` : '');
}

function replaceEmerald(match, variant, prop, shade, opacity) {
  const target = EMERALD_MAP[shade];
  if (!target) return match; // unknown emerald shade, skip
  return `${variant ?? ''}${prop}-[var(--color-${target})]` + (opacity ? `/${opacity}` : '');
}

function replaceCustom(match, variant, prop, palette, shade, opacity) {
  return `${variant ?? ''}${prop}-[var(--color-${palette}-${shade})]` + (opacity ? `/${opacity}` : '');
}

// ── Walk src/ ──
const ROOT = path.resolve(__dirname, '..', 'src');
const EXT = ['.tsx', '.ts'];
const modified = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fp = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!entry.name.startsWith('.')) walk(fp);
    } else if (EXT.includes(path.extname(entry.name))) {
      processFile(fp);
    }
  }
}

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  const original = content;

  // 1️⃣ Replace emerald-* → CSS variable
  content = content.replace(EMERALD_RE, replaceEmerald);

  // 2️⃣ Replace custom palette shorthands → CSS variable
  content = content.replace(CUSTOM_RE, replaceCustom);

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf8');
    modified.push(filePath);
  }
}

console.log('Starting color standardization...\n');
walk(ROOT);

if (modified.length === 0) {
  console.log('No files needed updating.');
} else {
  console.log(`Updated ${modified.length} file(s):\n`);
  for (const f of modified) {
    const rel = path.relative(path.join(__dirname, '..', 'frontend'), f);
    console.log(`  ${rel}`);
  }
}
console.log('\nDone. Run tsc --noEmit and eslint to verify.');
