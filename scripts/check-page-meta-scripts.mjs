/**
 * Screen a translation table for characters that are outside a locale's script.
 *
 * Run before applying: a single Chinese glyph in an Arabic row is the same class
 * of mistake as the original mojibake files, and it passes every structural check.
 */
const TABLES = [
  ['./page-meta-scripts-engine.mjs', 'PAGE_META'],
  ['./page-meta-scripts-marketplace.mjs', 'PAGE_META'],
  ['./page-meta-latin-marketplace.mjs', 'PAGE_META'],
];

const SCRIPT_RANGES = {
  ar: [[0x0600, 0x06ff]],
  ur: [[0x0600, 0x06ff]],
  ru: [[0x0400, 0x04ff]],
  zh: [
    [0x4e00, 0x9fff],
    [0x3000, 0x303f],
    [0xff00, 0xffef],
  ],
  hi: [[0x0900, 0x097f]],
  bn: [[0x0980, 0x09ff]],
};

/** Latin, Cyrillic, Arabic, Indic, CJK, punctuation and spaces are all fine. */
const NEIGHBOURS = [
  [0x0020, 0x007f],
  [0x00a0, 0x00ff],
  [0x0100, 0x017f],
  [0x0400, 0x04ff],
  [0x0590, 0x06ff],
  [0x0900, 0x0dff],
  [0x2000, 0x206f],
  [0x20a0, 0x20bf],
  [0x3000, 0x303f],
  [0x4e00, 0x9fff],
  [0xfb50, 0xfdff],
  [0xfe70, 0xfeff],
  [0xff00, 0xffef],
];

const inRanges = (code, ranges) => ranges.some(([low, high]) => code >= low && code <= high);

let problems = 0;

for (const [file, exportName] of TABLES) {
  const module_ = await import(file);
  const table = module_[exportName];
  for (const [locale, entries] of Object.entries(table)) {
    const own = SCRIPT_RANGES[locale];
    if (!own) continue;
    for (const [slug, pair] of Object.entries(entries)) {
      if (!Array.isArray(pair) || pair.length !== 2) {
        console.log(`INCOMPLETE  ${locale}.${slug}`);
        problems += 1;
        continue;
      }
      for (const [field, value] of [
        ['title', pair[0]],
        ['description', pair[1]],
      ]) {
        for (const char of value) {
          const code = char.codePointAt(0);
          if (inRanges(code, own) || inRanges(code, NEIGHBOURS)) continue;
          console.log(
            `SUSPECT    ${locale}.${slug}.${field}: ${char} (U+${code.toString(16).toUpperCase()})`,
          );
          problems += 1;
          break;
        }
      }
    }
  }
}

console.log(problems === 0 ? 'script affinity: clean' : `script affinity: ${problems} problem(s)`);
process.exit(problems === 0 ? 0 : 1);
