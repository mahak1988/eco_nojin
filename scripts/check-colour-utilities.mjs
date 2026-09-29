/**
 * Reports Tailwind colour utilities in the tree that name no defined token.
 *
 * The theme block in `src/app/globals.css` declares eighteen colours. Tailwind 4
 * silently drops a utility whose theme key does not exist, so `bg-primary`
 * compiles, type-checks, passes Biome, passes the a11y suite and renders nothing.
 * That is the worst failure mode in a token-driven design system: the class
 * reads as styling and is not styling.
 *
 * `check-ui-kit.mjs` catches physical CSS and hard-coded copy. It does not know
 * whether a token exists, so this is the missing half of the same rule.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const WEB = process.argv[2];
if (!WEB) {
  console.error('usage: node find-undefined-tokens.mjs <apps/web directory>');
  process.exit(2);
}

const css = readFileSync(join(WEB, 'src', 'app', 'globals.css'), 'utf8');
const themeBlock = css.slice(css.indexOf('@theme'), css.indexOf('@layer'));
const defined = new Set(
  [...themeBlock.matchAll(/--color-([a-z0-9-]+):/g)].map((m) => m[1]),
);

/** Tailwind colour utility prefixes that resolve to `--color-<name>`. */
const PREFIXES = [
  'bg',
  'text',
  'border',
  'ring',
  'fill',
  'stroke',
  'from',
  'via',
  'to',
  'shadow',
  'outline',
  'decoration',
  'accent',
  'caret',
  'divide',
  'placeholder',
];

// Utilities that share a prefix with a colour but are not one.
const NOT_COLOURS = new Set([
  'text-sm',
  'text-xs',
  'text-base',
  'text-lg',
  'text-xl',
  'text-2xl',
  'text-3xl',
  'text-4xl',
  'text-5xl',
  'text-6xl',
  'text-7xl',
  'text-9xl',
  'text-center',
  'text-start',
  'text-end',
  'text-left',
  'text-right',
  'text-justify',
  'text-balance',
  'text-pretty',
  'text-ellipsis',
  'text-clip',
  'text-wrap',
  'text-nowrap',
  'text-opacity',
  'text-mono',
  'text-sans',
  'text-display',
  'text-num',
  'text-inherit',
  'text-current',
  'text-transparent',
  'text-black',
  'text-white',
  'border-none',
  'border-solid',
  'border-dashed',
  'border-dotted',
  'border-double',
  'border-hidden',
  'border-collapse',
  'border-separate',
  'border-transparent',
  'border-current',
  'bg-none',
  'bg-transparent',
  'bg-current',
  'bg-black',
  'bg-white',
  'bg-auto',
  'bg-cover',
  'bg-contain',
  'bg-repeat',
  'bg-no-repeat',
  'bg-fixed',
  'bg-local',
  'bg-scroll',
  'bg-center',
  'bg-top',
  'bg-bottom',
  'bg-left',
  'bg-right',
  'border-0',
  'border-2',
  'border-4',
  'border-8',
  'border-t',
  'border-b',
  'border-l',
  'border-r',
  'border-x',
  'border-y',
  'border-s',
  'border-e',
  'divide-x',
  'divide-y',
  'divide-x-reverse',
  'divide-y-reverse',
  'decoration-none',
  'decoration-solid',
  'decoration-double',
  'decoration-dotted',
  'decoration-dashed',
  'decoration-wavy',
  'decoration-underline',
  'decoration-overline',
  'decoration-line-through',
  'decoration-auto',
  'ring-0',
  'ring-1',
  'ring-2',
  'ring-4',
  'ring-8',
  'shadow-sm',
  'shadow-md',
  'shadow-lg',
  'shadow-xl',
  'shadow-2xl',
  'shadow-card',
  'shadow-pop',
  'shadow-none',
  'shadow-inner',
]);

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (/\.(tsx|ts|css)$/.test(name)) acc.push(full);
  }
  return acc;
}

const findings = new Map();
for (const file of walk(join(WEB, 'src'))) {
  const source = readFileSync(file, 'utf8');
  const lines = source.split('\n');
  lines.forEach((line, index) => {
    // A colour utility only matters where a class list can be, so the search is
    // scoped to quoted or bracketed runs rather than the whole file.
    for (const block of line.matchAll(/["'`]([^"'`]*\s(?:[a-z][a-z0-9:/\[\]._-]*\s)+[^"'`]*)["'`]/g)) {
      for (const token of block[1].split(/\s+/)) {
        const match = /^([a-z-]+)-(.+)$/.exec(token);
        if (!match) continue;
        const [, prefix, rest] = match;
        if (!PREFIXES.includes(prefix)) continue;
        if (NOT_COLOURS.has(token)) continue;
        // A modifier means the real key is the part before the slash.
        const base = rest.split('/')[0];
        // Skip sizes, widths, opacities and arbitrary values.
        if (
          /^(\d|px|auto|full|screen|min|max|fit|inherit|none|current|transparent|black|white|\[)/.test(
            base,
          )
        ) {
          continue;
        }
        if (/^[a-z]+-\d+$/.test(base)) continue;
        if (defined.has(base)) continue;
        if (!findings.has(base)) findings.set(base, new Set());
        findings.get(base).add(`${relative(WEB, file)}:${index + 1}`);
      }
    }
  });
}

console.log(`theme declares ${defined.size} colours: ${[...defined].sort().join(', ')}`);
if (findings.size === 0) {
  console.log('every colour utility resolves to a declared token');
  process.exit(0);
}
console.log(`\n${findings.size} colour utility name(s) resolve to no token:`);
for (const [token, files] of [...findings].sort((a, b) => b[1].size - a[1].size)) {
  console.log(`  ${token}  (${files.size} file(s))`);
  for (const file of [...files].slice(0, 6)) console.log(`      ${file}`);
  if (files.size > 6) console.log(`      ... and ${files.size - 6} more`);
}
process.exit(1);
