/**
 * WCAG 2.2 contrast for the token pairs the UI kit actually paints.
 *
 * The master plan makes accessibility binding ("WCAG 2.2 AA برای همهٔ بافتها"),
 * and the palette was tuned by eye, so six of the pairs the components ship
 * missed their floor — most of them only in dark mode, where the contextual
 * colours are the light branch. `text-paper` on `bg-forest`, the pair nine
 * action surfaces used, measured 1.07:1 in light mode. Nothing in the suite could
 * see that: the classes resolved, the components compiled, and the tokens are
 * declared, so every existing gate reported the design system as conformant.
 *
 * This gate converts the declared `light-dark()` pairs to sRGB, computes
 * relative luminance, and checks the ratio. It reads the real values out of
 * `globals.css` rather than restating them, so a token edit that breaks
 * contrast fails here instead of shipping.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const WEB = join(dirname(dirname(fileURLToPath(import.meta.url))), 'apps', 'web');
const css = readFileSync(join(WEB, 'src', 'app', 'globals.css'), 'utf8');

function toLinear(L, C, hDeg) {
  const h = (hDeg * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
}
const ch = (c) => {
  const v = Math.min(1, Math.max(0, c));
  return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
};
const lum = (rgb) => 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2]);
const ratio = (a, b) => (Math.max(lum(a), lum(b)) + 0.05) / (Math.min(lum(a), lum(b)) + 0.05);

const tokens = new Map();
for (const match of css.matchAll(/--([a-z0-9-]+):\s*light-dark\(/g)) {
  let depth = 1;
  let i = match.index + match[0].length;
  const start = i;
  while (i < css.length && depth > 0) {
    if (css[i] === '(') depth += 1;
    else if (css[i] === ')') depth -= 1;
    i += 1;
  }
  const body = css.slice(start, i - 1);
  let d = 0;
  let cut = -1;
  for (let k = 0; k < body.length; k += 1) {
    if (body[k] === '(') d += 1;
    else if (body[k] === ')') d -= 1;
    else if (body[k] === ',' && d === 0) {
      cut = k;
      break;
    }
  }
  const parse = (text) => {
    const p = /oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)/.exec(text);
    return toLinear(+p[1], +p[2], +p[3]);
  };
  tokens.set(match[1], { light: parse(body.slice(0, cut)), dark: parse(body.slice(cut + 1)) });
}
for (const match of css.matchAll(/--([a-z0-9-]+):\s*var\(--([a-z0-9-]+)\)\s*;/g)) {
  if (!tokens.has(match[1]) && tokens.has(match[2])) tokens.set(match[1], tokens.get(match[2]));
}
// A token with a single value is scheme-invariant.
for (const match of css.matchAll(/--([a-z0-9-]+):\s*(oklch\([^;]+\));/g)) {
  if (tokens.has(match[1])) continue;
  const rgb = toLinear(.../oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)/.exec(match[2]).slice(1, 4).map(Number));
  tokens.set(match[1], { light: rgb, dark: rgb });
}

const PAIRS = [
  ['link / accent text on the page', 'forest', 'canvas', 4.5],
  ['link / accent text on a card', 'forest', 'surface', 4.5],
  ['error text on a field', 'danger', 'surface', 4.5],
  ['error text on the page', 'danger', 'canvas', 4.5],
  ['body text on the page', 'ink', 'canvas', 4.5],
  ['body text on a card', 'ink', 'surface', 4.5],
  ['secondary text on the page', 'ink-soft', 'canvas', 4.5],
  ['secondary text on a card', 'ink-soft', 'surface', 4.5],
  ['faint text on the page', 'ink-faint', 'canvas', 4.5],
  ['faint text on a card', 'ink-faint', 'surface', 4.5],
  ['action label on the action colour', 'on-action', 'action', 4.5],
  ['warning banner label on copper', 'on-action', 'copper', 4.5],
  ['info banner label on water', 'on-action', 'water', 4.5],
  ['the danger token against a field', 'danger', 'surface', 4.5],
  ['the danger token against the page', 'danger', 'canvas', 4.5],
  ['the clay error copy on a card', 'clay', 'surface', 4.5],
  ['the clay error copy on the page', 'clay', 'canvas', 4.5],
  ['the clay error boundary on a card', 'clay', 'surface', 3.0],
  ['field boundary on the page', 'line-strong', 'canvas', 3.0],
  ['field boundary on a card', 'line-strong', 'surface', 3.0],
  ['hairline divider (decorative)', 'line', 'canvas', 1.0],
];

/**
 * Pairings that are measured and reported but never required to pass.
 *
 * The contextual colours are the light branch in dark mode, so a fixed light
 * label on them clears AA in one scheme and misses it in the other. The
 * measurement is printed so the number is on the record next to the token, and
 * so anyone reaching for the pairing sees why `--action` exists — but a palette
 * is not obliged to offer every combination, and failing the build on a pair
 * nothing uses would be theatre.
 */
const NOT_OFFERED = [
  ['a light label on the contextual green', 'on-action', 'forest'],
  ['a light label on the contextual clay', 'on-action', 'clay'],
];

let failures = 0;
console.log('pair                                  light   dark   floor');
for (const [label, fg, bg, floor] of PAIRS) {
  const f = tokens.get(fg);
  const b = tokens.get(bg);
  if (!f || !b) {
    console.log(`${label.padEnd(38)}  (token missing: ${!f ? fg : bg})`);
    failures += 1;
    continue;
  }
  const light = ratio(f.light, b.light);
  const dark = ratio(f.dark, b.dark);
  const bad = light < floor || dark < floor;
  if (bad) failures += 1;
  console.log(
    `${label.padEnd(38)}  ${light.toFixed(2).padStart(5)}  ${dark.toFixed(2).padStart(5)}  ${String(floor).padStart(5)}  ${bad ? 'FAIL' : 'ok'}`,
  );
}

if (failures > 0) {
  console.error(`\n${failures} pair(s) below their floor`);
  process.exit(1);
}

console.log('\nnot offered — measured for the record, not required to pass:');
for (const [label, fg, bg] of NOT_OFFERED) {
  const f = tokens.get(fg);
  const b = tokens.get(bg);
  if (!f || !b) {
    console.log(`  ${label.padEnd(38)}  (token missing)`);
    continue;
  }
  const light = ratio(f.light, b.light);
  const dark = ratio(f.dark, b.dark);
  const worst = Math.min(light, dark);
  console.log(
    `  ${label.padEnd(38)}  ${light.toFixed(2).padStart(5)}  ${dark.toFixed(2).padStart(5)}   ` +
      `worst ${worst.toFixed(2)}:1 — use --action as the surface instead`,
  );
}

console.log('\nall measured pairs meet their floor');
