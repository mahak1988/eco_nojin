import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Find mis-decoded UTF-8 in the source.
 *
 * The pattern is the one the original mojibake catalogues were made of: a Latin
 * letter followed by a codepoint in the Arabic Presentation Forms block, which is
 * what a UTF-8 byte sequence looks like after being decoded as cp1256. The cover
 * page had `'\u00e2\u20ac\u201d'` where an em dash belonged, which renders as
 * three characters on screen.
 */
const SRC = 'apps/web/src';
const TESTS = 'apps/web/tests';
const MESSAGES = 'apps/web/messages';

const MOJIBAKE = /[\u00c2-\u00c3][\ufb50-\ufdff\ufe70-\ufeff]|\u00e2[\u20ac\u201c\u201d\u00a0]|\u00c2[\u00a0\u00ab\u00bb]|\u00ef\u00bf\u00bd/;

function walk(dir, acc = []) {
  for (const item of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, item.name);
    if (item.isDirectory()) walk(full, acc);
    else if (/\.(ts|tsx|json)$/.test(item.name)) acc.push(full);
  }
  return acc;
}

let found = 0;
let exempt = 0;

/**
 * A file that legitimately contains the sequences it searches for.
 *
 * `tests/rtl.spec.ts` asserts that no rendered page contains `â€` or `Ã©`, so it
 * has to name them. Exempting it by path, with the reason recorded, is better
 * than loosening the pattern for everything.
 */
const EXEMPT = new Map([
  ['apps/web/tests/rtl.spec.ts', 'contains the mojibake signatures it asserts against'],
]);

for (const root of [SRC, TESTS, MESSAGES]) {
  for (const file of walk(root)) {
    const relative = file.replace(/\\/g, '/');
    const exemption = EXEMPT.get(relative);
    const text = readFileSync(file, 'utf8');
    text.split('\n').forEach((line, index) => {
      if (!MOJIBAKE.test(line)) return;
      if (exemption) {
        exempt += 1;
        return;
      }
      found += 1;
      const at = MOJIBAKE.exec(line).index;
      console.log(
        `${relative}:${index + 1}  ${JSON.stringify(line.slice(Math.max(0, at - 20), at + 24))}`,
      );
    });
  }
}

if (exempt > 0) {
  console.log(`${exempt} line(s) exempt: a file that names the signatures it searches for`);
}
console.log(found === 0 ? 'no mis-decoded UTF-8 found' : `${found} line(s) with mis-decoded UTF-8`);
process.exit(found === 0 ? 0 : 1);
