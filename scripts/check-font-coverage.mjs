#!/usr/bin/env node
/**
 * Reports which of the fourteen official locales are served by a font this
 * repository actually ships, and fails on anything less than that.
 *
 * It also fails on the two ways a *correct* font set can still fail to reach a
 * reader, both of which were live defects and neither of which a count of
 * `@font-face` blocks can see:
 *
 *   1. the rules live in a stylesheet every locale loads. 97 CJK
 *      `unicode-range` rules in `globals.css` cost every page in all fourteen
 *      locales 18.7 kB brotli for glyphs ten of them cannot render — the one
 *      −18.7 margin in the master plan §3.2 budget. So the script-family rules
 *      live in `public/styles/fonts/<locale>.css` and are linked per locale,
 *      and the compiled size of the global sheet is measured and capped here.
 *   2. the rules are written in a spelling the production build's CSS minifier
 *      corrupts, so the built stylesheet ships a face the browser throws away.
 *      See `UNSAFE_RANGE_END` below.
 *
 * Why this is a gate and not a note
 * ---------------------------------
 * `globals.css` bundled three families — Vazirmatn and Markazi Text for Arabic,
 * JetBrains Mono for Latin — which cover ten of the fourteen locales. The other
 * four write in scripts none of them reaches: Devanagari (`hi`), Bengali (`bn`),
 * CJK (`zh`) and Nastaliq (`ur`).
 *
 * Those four were first "solved" by naming a family in a `--font-sans-*` token:
 *
 *     --font-sans-deva: "Noto Sans Devanagari", "Nirmala UI", "Mangal", var(--font-sans);
 *
 * which passes every check a reader of the stylesheet would make, and serves
 * nothing. The name resolves, the stack is declared, the gate was green — and
 * the glyphs were whatever the reader's operating system happened to own, with
 * no control over weight, line height or digit form. A name that resolves while
 * providing nothing is the exact failure this repository is built to refuse, so
 * naming a family is now reported as `named, not present` and fails the build.
 *
 * What "bundled" means here
 * -------------------------
 * A family counts as bundled only when all three of these hold:
 *
 *   1. a `@font-face` in `globals.css` or in that locale's sheet declares it;
 *   2. that face's `src` points at `/fonts/…`, i.e. this origin and not a
 *      third-party CDN;
 *   3. the file behind that `src` exists in `apps/web/public/fonts`.
 *
 * (3) is the check that turns a declaration into a delivery. Without it a
 * `@font-face` pointing at a file nobody ever copied into `public/` is
 * indistinguishable, to every tool in the chain, from a working font.
 *
 * Overridable so the gate can be run against a doctored stylesheet in a test:
 * `ECO_CSS_FILE` (the global sheet) and `ECO_FONT_SHEET_DIR` (the per-locale
 * sheets). Font files are still resolved against the real `public/fonts` on
 * purpose — a doctored stylesheet is a claim about CSS, not a licence to
 * pretend the bytes are missing too.
 */
import { existsSync, readFileSync, statSync, writeSync } from 'node:fs';
import { createRequire } from 'node:module';
import { basename, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { brotliCompressSync, constants } from 'node:zlib';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB = join(REPO_ROOT, 'apps', 'web');
const CSS = process.env.ECO_CSS_FILE ?? join(WEB, 'src', 'app', 'globals.css');
/** Where `/styles/fonts/<locale>.css` resolves, and therefore where the sheets live. */
const FONT_SHEET_DIR =
  process.env.ECO_FONT_SHEET_DIR ?? join(WEB, 'public', 'styles', 'fonts');
/** The one file that decides which per-locale sheet a page links. */
const LAYOUT = join(WEB, 'src', 'app', '[locale]', 'layout.tsx');
/** Where the runtime font cache is budgeted. */
const SW = join(WEB, 'src', 'app', 'sw.ts');
/** Where `/fonts/…` resolves at runtime, and therefore where the bytes must be. */
const PUBLIC_FONTS = join(WEB, 'public', 'fonts');

/** Which script each bundled family actually carries. */
const BUNDLED_SCRIPT = {
  Vazirmatn: 'Arabic',
  'Markazi Text': 'Arabic',
  'JetBrains Mono': 'Latin',
  'Noto Sans Devanagari': 'Devanagari',
  'Noto Sans Bengali': 'Bengali',
  'Noto Nastaliq Urdu': 'Nastaliq',
  'Noto Sans SC': 'CJK',
};

/**
 * The families allowed to stay in `globals.css`.
 *
 * These three are the majority-script faces: two of them also carry the Latin
 * cut, so every one of the fourteen locale stacks — each of which ends in
 * `var(--font-sans)` — can reach Latin from this stylesheet, and ten locales
 * need nothing else. The other four families are readable by exactly one locale
 * each and belong in that locale's sheet.
 */
const GLOBAL_FAMILIES = new Set(['Vazirmatn', 'Markazi Text', 'JetBrains Mono']);

/**
 * Budgets for the sheet that all fourteen locales load, both measured with the
 * project's own pipeline — `postcss([@tailwindcss/postcss])` and then the
 * `cssnano-simple` minimizer Next bundles, i.e. the bytes a browser downloads
 * after a production build.
 *
 * Two numbers, because the sheet is two things:
 *
 *   `rawBytes` / `brotliBytes` cap the whole sheet. Measured today at about
 *   72.8 kB raw / 11.6 kB brotli, of which roughly 69 kB is Tailwind's utilities
 *   for the whole app — a number that grows whenever a component is added, and
 *   that this gate has no business holding still. So it is set with room to
 *   grow (110 kB / 19 kB) while staying well under the 160.3 kB / 29.6 kB the
 *   same sheet measures with the script families in it: a regression of that
 *   shape fails this by 1.5x rather than by a rounding error.
 *
 *   `fontBytes` caps the `@font-face` rules inside that sheet, which is the part
 *   this gate is about and the part a locale can be charged or spared. Three
 *   majority-script families are 12 rules and about 3.6 kB minified; the four
 *   script families are 100 rules and about 93.6 kB. 12 kB is the ceiling, so
 *   moving a script family back into the global sheet fails by a factor of
 *   eight on this number alone.
 *
 * It is a byte budget, not a count of rules: 97 CJK rules that gzip well and
 * 12 fat ones that do not are the same defect, and only the bytes see it.
 */
const GLOBAL_SHEET_BUDGET = { rawBytes: 110_000, brotliBytes: 19_000, fontBytes: 12_000 };


/**
 * A `unicode-range` range whose *end* is `0x…FF` is rewritten by the build's CSS
 * minifier into a literal `?`: `U+0600-06FF` comes out of lightningcss as
 * `U+6??`, and 14 of the 112 declarations in the stylesheet a build on this
 * machine wrote to `.next/static/css/` are written that way — every face in the
 * global sheet, the whole of `Noto Nastaliq Urdu`, and one CJK slice.
 *
 * `?` is not part of a `<urange>` in css-values-4, so those declarations are
 * only understood because an engine chooses to be lenient about them. Measured
 * in Chromium and in WebKit, both of which re-read `U+6??` as `U+600-6FF` — the
 * identical codepoint set — and both of which then download and use the face
 * anyway. Firefox is not installed on this machine, so it was not measured.
 *
 * So this is a rule about not depending on an engine's leniency, not a repair
 * of a broken build: the source is spelled so the minifier has nothing to
 * rewrite. The fix is a spelling change, not a range change — write
 * `U+0600-06FE, U+06FF`, the same codepoints split so no range ends in `FF` —
 * and 43 ranges across the five stylesheets are spelled that way.
 */
const UNSAFE_RANGE_END = /U\+[0-9A-Fa-f]+-[0-9A-Fa-f]*ff\b/i;


/** The fourteen official locales and the bundled family that serves each. */
const LOCALE_FAMILY = {
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
  hi: 'Noto Sans Devanagari',
  bn: 'Noto Sans Bengali',
  zh: 'Noto Sans SC',
  ur: 'Noto Nastaliq Urdu',
};

/** The four locales that needed a family of their own, and the token that reaches it. */
const SCRIPT_STACKS = {
  hi: { stack: '--font-sans-deva', script: 'Devanagari', family: 'Noto Sans Devanagari' },
  bn: { stack: '--font-sans-beng', script: 'Bengali', family: 'Noto Sans Bengali' },
  zh: { stack: '--font-sans-cjk', script: 'CJK', family: 'Noto Sans SC' },
  ur: {
    stack: '--font-sans-nastaliq',
    script: 'Nastaliq',
    family: 'Noto Nastaliq Urdu',
  },
};

/**
 * One codepoint per script that any face claiming to cover the script must
 * reach. Without this, a family could be "bundled" through its Latin slice
 * alone — the file would be on disk, the locale would be green, and every
 * Devanagari glyph would still come from the reader's operating system.
 */
const SCRIPT_PROBE = {
  Arabic: [0x0627], // ARABIC LETTER ALEF
  Latin: [0x0041], // LATIN CAPITAL LETTER A
  Devanagari: [0x0915], // DEVANAGARI LETTER KA — the first letter of `hi`
  Bengali: [0x0995], // BENGALI LETTER KA — the first letter of `bn`
  Nastaliq: [0x0627, 0x06a9], // ALEF, KAF — `ur` and Nastaliq's own letters
  CJK: [0x4e00, 0x6c34], // 一, 水 — the commonest and the platform's own subject
};

const css = readFileSync(CSS, 'utf8');

/** The per-locale sheets, in the order the report prints them. */
const SCRIPT_LOCALES = Object.keys(SCRIPT_STACKS);

/**
 * Every stylesheet that declares a bundled face, keyed by the name the report
 * uses for it. `globals.css` is the one all fourteen locales load; the rest are
 * loaded by a single locale each.
 */
const sheets = new Map([['globals.css', css]]);
for (const locale of SCRIPT_LOCALES) {
  const file = join(FONT_SHEET_DIR, `${locale}.css`);
  if (!existsSync(file)) {
    sheets.set(`${locale}.css`, null);
    continue;
  }
  sheets.set(`${locale}.css`, readFileSync(file, 'utf8'));
}

/*
 * Comments are stripped before anything is parsed.
 *
 * Not a nicety: a `/* … *\/`-wrapped `@font-face` is the most natural way to
 * disable one of these faces while working, and a parser that reads the raw
 * text finds a declaration inside it and reports the family as bundled. That
 * is the same class of error as the one this gate exists to catch — a name that
 * is present in the file and absent from the page — and it was found by
 * commenting a face out and re-running this script.
 */
const strip = (text) => (text ?? '').replace(/\/\*[\s\S]*?\*\//g, '');

/** The global sheet with its comments removed. Kept separate: some rules read it. */
const live = strip(css);

/** `@font-face` rules in one stylesheet, with the parts this gate cares about. */
function parseFaces(text) {
  return [...strip(text).matchAll(/@font-face\s*\{([^}]*)\}/g)].map((match) => {
    const body = match[1];
    return {
      family: /font-family:\s*["']([^"']+)["']/.exec(body)?.[1],
      display: /font-display:\s*([\w-]+)/.exec(body)?.[1],
      range: /unicode-range:\s*([^;}]+)/.exec(body)?.[1]?.replace(/\s+/g, ' ').trim(),
      urls: [...body.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)].map((u) => u[1]),
    };
  });
}

/** Every `@font-face` this origin serves, across every sheet, tagged with its sheet. */
const faces = [...sheets.entries()].flatMap(([sheet, text]) =>
  parseFaces(text).map((face) => ({ ...face, sheet })),
);


/** Does a `unicode-range` declaration cover this codepoint? */
function rangeCovers(range, codepoint) {
  if (!range) return false;
  return range.split(',').some((part) => {
    const token = part.trim().replace(/^U\+/i, '');
    if (token.includes('-')) {
      const [from, to] = token.split('-');
      return codepoint >= Number.parseInt(from, 16) && codepoint <= Number.parseInt(to, 16);
    }
    return codepoint === Number.parseInt(token, 16);
  });
}

/** The `@font-face` bodies of one family, or nothing if it is not declared at all. */
const familyFaces = new Map();
for (const face of faces) {
  if (!BUNDLED_SCRIPT[face.family]) continue;
  if (!familyFaces.has(face.family)) familyFaces.set(face.family, []);
  familyFaces.get(face.family).push(face);
}

/** Families named in a `font-family` list, in order, ignoring the generic tail. */
function namesIn(value) {
  return value
    .replace(/\s+/g, ' ')
    .split(',')
    .map((part) => part.trim().replace(/^["']|["']$/g, ''))
    .filter(Boolean);
}

/** The stylesheets that declare a family, for error messages that must name one. */
function sheetsDeclaring(family) {
  return [...new Set((familyFaces.get(family) ?? []).map((face) => face.sheet))];
}

const errors = [];
const rows = [];
/** Every distinct file the stylesheets point at, so the totals are not per-locale. */
const served = new Set();

for (const [locale, family] of Object.entries(LOCALE_FAMILY)) {
  const script = BUNDLED_SCRIPT[family];
  const declared = familyFaces.get(family) ?? [];
  // A self-hosted src is one this origin serves: `/fonts/…`, not a CDN.
  const selfHosted = declared
    .flatMap((face) => face.urls)
    .filter((url) => url.startsWith('/fonts/'));
  const onDisk = selfHosted
    .map((url) => url.replace(/^\//, ''))
    .filter((relative) => existsSync(join(WEB, 'public', relative)));

  if (selfHosted.length === 0) {
    const where = sheetsDeclaring(family);
    errors.push(
      declared.length > 0
        ? `${locale} needs ${script}, and "${family}" is declared by @font-face but no face in ` +
            `${where.length > 0 ? where.join(', ') : 'any sheet'} has a self-hosted src, so the reader ` +
            `gets their own font. Give it a src: url("/fonts/…").`
        : `${locale} needs ${script}, and no @font-face in any stylesheet declares "${family}". ` +
            `Bundle it, or map the locale to a family that is bundled.`,
    );
    rows.push(`  ${locale.padEnd(4)} NAMED ONLY  ${family} (${script})`);
    continue;
  }

  if (onDisk.length === 0) {
    const missing = [...new Set(selfHosted)].join(', ');
    errors.push(
      `${locale} needs ${script}, and every @font-face for "${family}" points at ${missing}, ` +
        `which is not in apps/web/public/fonts. The face is named and provides nothing.`,
    );
    rows.push(`  ${locale.padEnd(4)} NOT ON DISK ${family} (${script})`);
    continue;
  }

  // A family can be "bundled" through its Latin slice alone: the file would be on
  // disk, the locale green, and every Devanagari glyph still the reader's.
  const probes = SCRIPT_PROBE[script] ?? [];
  const missingProbes = probes.filter(
    (codepoint) => !declared.some((face) => rangeCovers(face.range, codepoint)),
  );
  if (missingProbes.length > 0) {
    errors.push(
      `${locale} needs ${script}, but the bundled faces of "${family}" do not cover ` +
        `${missingProbes.map((c) => `U+${c.toString(16).toUpperCase()}`).join(', ')}. ` +
        `A Latin-only slice of a ${script} family still leaves the reader's font in charge.`,
    );
    rows.push(`  ${locale.padEnd(4)} WRONG SLICE ${family} (${script})`);
    continue;
  }

  for (const relative of onDisk) served.add(relative);
  const bytes = onDisk.reduce(
    (total, relative) => total + statSync(join(WEB, 'public', relative)).size,
    0,
  );
  rows.push(
    `  ${locale.padEnd(4)} bundled      ${family.padEnd(21)} ` +
      `${String(declared.length).padStart(3)} face(s)  ${bytes.toLocaleString('en-US').padStart(9)} B  ` +
      `${script.padEnd(11)} in ${sheetsDeclaring(family).join(' + ')}`,
  );
}

// 1. Every @font-face that points into /fonts/ must name a file that is there.
//    A dangling src is the quiet half of "provides nothing": the gate would
//    report the family as bundled while every request 404s.
for (const face of faces) {
  for (const url of face.urls.filter((u) => u.startsWith('/fonts/'))) {
    if (!existsSync(join(WEB, 'public', url.replace(/^\//, '')))) {
      errors.push(
        `@font-face for "${face.family}" points at ${url}, which is not in apps/web/public/fonts`,
      );
    }
  }
}

// 2. Every bundled face must declare `font-display` and a `unicode-range`. A
//    face with no range is downloaded by every page regardless of its script,
//    and a face with no `font-display` blocks first paint on an invisible font.
for (const [family, declared] of familyFaces) {
  for (const face of declared) {
    if (!face.urls.some((url) => url.startsWith('/fonts/'))) continue;
    if (face.display !== 'swap') {
      errors.push(
        `@font-face for "${family}" (${basename(face.urls[0] ?? '?')}) does not set font-display: swap`,
      );
    }
    if (!face.range) {
      errors.push(
        `@font-face for "${family}" (${basename(face.urls[0] ?? '?')}) has no unicode-range, so a ` +
          `browser will download it for any character it can render`,
      );
    }
  }
}

// 3. Every script stack must reach a real family, and reach *our* family first.
//    Naming a reader-installed face ahead of the bundled one would let
//    `Microsoft YaHei` or `PingFang SC` win on exactly the readers we bundled
//    a font for.
for (const [locale, info] of Object.entries(SCRIPT_STACKS)) {
  const declaration = new RegExp(`${info.stack}:\\s*([^;]+);`).exec(live);
  if (!declaration) {
    errors.push(
      `${locale} needs the ${info.script} script and no ${info.stack} stack is declared for it. ` +
        `Add one, or bundle a font.`,
    );
    continue;
  }
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
  const first = namesIn(value)[0];
  if (first !== info.family) {
    errors.push(
      `${locale}: ${info.stack} starts with "${first}", not the bundled "${info.family}". ` +
        `A reader who has "${first}" installed would be served that instead of ours.`,
    );
  }
}

// 4. The per-locale selectors must exist, or the stack is declared and unused.
//    The attribute selector is matched with a tolerant quote pattern: Biome
//    normalises `html[lang='hi']` to `html[lang="hi"]`, so a single-quoted search
//    would report every one of these as missing.
for (const locale of Object.keys(SCRIPT_STACKS)) {
  const selector = new RegExp(`html\\[lang=['"]${locale}['"]\\]`);
  if (!selector.test(live)) {
    errors.push(
      `${locale} has a font stack but no html[lang] rule, so the stack is never applied`,
    );
  }
}

// 5. Each script locale's sheet must exist and hold that locale's family.
//    A family with no sheet at all is the quietest failure in this file: the
//    locale row above is computed from the union of every sheet, so it would
//    still read `bundled` while the browser was served a 404 for the sheet.
for (const locale of SCRIPT_LOCALES) {
  const name = `${locale}.css`;
  if (sheets.get(name) === null) {
    errors.push(
      `public/styles/fonts/${name} does not exist, so a ${locale} page is served no ` +
        `@font-face for "${SCRIPT_STACKS[locale].family}" and falls back to the reader's font`,
    );
    continue;
  }
  const wanted = SCRIPT_STACKS[locale].family;
  const inSheet = new Set(parseFaces(sheets.get(name)).map((face) => face.family));
  if (!inSheet.has(wanted)) {
    errors.push(
      `public/styles/fonts/${name} declares ${[...inSheet].join(', ') || 'no family'}, but a ` +
        `${locale} page needs "${wanted}"`,
    );
  }
  for (const family of inSheet) {
    if (LOCALE_FAMILY[locale] === family) continue;
    errors.push(
      `public/styles/fonts/${name} declares "${family}", which no ${locale} page asks for. ` +
        `A ${locale} reader downloads those rules for nothing.`,
    );
  }
}

// 6. A family only one script reads must not be in the global sheet. This is
//    the check that keeps the 18.7 kB brotli where it belongs: `globals.css` is
//    linked by every page of every locale, so a CJK rule in it is 97 rules of
//    cost on a page in `de` that can never use one of them. The size budget
//    below catches the symptom; this catches the cause.
for (const family of familyFaces.keys()) {
  if (GLOBAL_FAMILIES.has(family)) continue;
  const readers = Object.entries(LOCALE_FAMILY)
    .filter(([, mapped]) => mapped === family)
    .map(([locale]) => locale);
  const strays = (familyFaces.get(family) ?? []).filter((face) => face.sheet === 'globals.css');
  if (strays.length === 0) continue;
  const where =
    strays.length === 1
      ? basename(strays[0].urls[0] ?? '?')
      : `${basename(strays[0].urls[0] ?? '?')} … ${basename(strays.at(-1).urls[0] ?? '?')}`;
  errors.push(
    `${strays.length} @font-face rule${strays.length === 1 ? '' : 's'} for "${family}" ` +
      `${strays.length === 1 ? 'is' : 'are'} declared in globals.css (${where}), but only ` +
      `${readers.join(', ')} read${readers.length === 1 ? 's' : ''} that script and globals.css is ` +
      `loaded by all ${Object.keys(LOCALE_FAMILY).length} locales. Move ${strays.length === 1 ? 'it' : 'them'} to ` +
      `public/styles/fonts/${readers[0]}.css.`,
  );
}

// 7. The global sheet must not pull a locale sheet back into the bundle, and the
//    layout must actually link each one. A sheet that exists and is never
//    requested is the same defect as a font that is named and never fetched.
if (/styles\/fonts\//.test(live)) {
  errors.push(
    'globals.css references a per-locale font sheet, which puts it back in the one stylesheet ' +
      'every locale loads. Link it from the layout instead',
  );
}
if (existsSync(LAYOUT)) {
  const layout = readFileSync(LAYOUT, 'utf8');
  for (const locale of SCRIPT_LOCALES) {
    if (!layout.includes(`/styles/fonts/${locale}.css`)) {
      errors.push(
        `app/[locale]/layout.tsx never links /styles/fonts/${locale}.css, so a ${locale} page ` +
          `loads the stack but not the face behind it`,
      );
    }
  }
}

// 8. No `unicode-range` may end a range in 0x…FF. The build's minifier rewrites
//    those into a `?` that only an engine's leniency understands. See
//    UNSAFE_RANGE_END for what was measured and what was not.
for (const face of faces) {
  if (!face.range) continue;
  if (UNSAFE_RANGE_END.test(face.range)) {
    errors.push(
      `${face.sheet}: @font-face for "${face.family}" (${basename(face.urls[0] ?? '?')}) has a ` +
        `unicode-range ending in 0xFF, which the build's CSS minifier rewrites to a "?" that no ` +
        `spec defines. Write the same codepoints as "U+start-(end-1), U+end".`,
    );
  }
  if (face.range.includes('?')) {
    errors.push(
      `${face.sheet}: @font-face for "${face.family}" has a "?" in its unicode-range, which is not ` +
        `part of a <urange> in css-values-4; whether a face is still used then depends on the engine`,
    );
  }
}

// 9. The runtime font cache must be able to hold every font this origin can
//    serve. `sw.ts` sized it at 112 entries — the number of distinct woff2 the
//    stylesheets reach — and a page that pulls ~20 CJK slices plus the Latin cut
//    is well inside that. The number is re-derived here rather than trusted,
//    because a budget that silently falls behind the font set brings back the
//    bug it was sized against: a `zh` session evicting slices it just used.
const reachableFonts = new Set(
  faces.flatMap((face) => face.urls.filter((url) => url.startsWith('/fonts/'))),
);
if (existsSync(SW)) {
  const sw = readFileSync(SW, 'utf8');
  const budget = /FONT_CACHE_MAX_ENTRIES\s*=\s*(\d+)/.exec(sw)?.[1];
  const reachable = reachableFonts.size;
  if (budget === undefined) {
    errors.push(
      'sw.ts declares no FONT_CACHE_MAX_ENTRIES, so fonts fall back to the shared static-asset ' +
        'budget of 80 entries with every js, css and image on the site',
    );
  } else if (Number(budget) < reachable) {
    errors.push(
      `sw.ts budgets the font cache at ${budget} entries but the stylesheets can reach ` +
        `${reachable} font files, so a reader who touches more than ${budget} of them starts ` +
        `evicting slices the current page just used. Raise FONT_CACHE_MAX_ENTRIES.`,
    );
  }
  if (!/cacheName:\s*'fonts-/.test(sw)) {
    errors.push(
      "sw.ts has no 'fonts-*' runtime cache, so font requests are served by the shared " +
        'static-asset route and its budget',
    );
  }
  const staticRoute = /matcher:\s*\/(?:[^/]*)\/i,/.exec(sw)?.[0] ?? '';
  if (/woff/.test(staticRoute)) {
    errors.push(
      'the static-asset route in sw.ts still matches woff/woff2, so a font can land in either ' +
        'cache. Remove the font extensions from that matcher; the font route owns them',
    );
  }
}

/*
 * Both streams are written with `writeSync`, not `console.log`.
 *
 * `console.log` to a pipe is asynchronous, so the table on stdout and the
 * problem list on stderr interleave arbitrarily when the output is captured —
 * the failure list appeared in the middle of the locale table, which reads as
 * though the table itself were broken. A gate people are meant to read has to
 * keep its own output in order.
 */
const out = (line) => writeSync(1, `${line}\n`);
const err = (line) => writeSync(2, `${line}\n`);

const servedBytes = [...served].reduce(
  (total, relative) => total + statSync(join(WEB, 'public', relative)).size,
  0,
);

out(
  `font coverage: ${familyFaces.size} families declared, ${served.size} distinct font files, ` +
    `${servedBytes.toLocaleString('en-US')} B on disk`,
);
for (const row of rows) out(row);

/** Brotli at the quality a CDN serves CSS at, which is how the budget is stated. */
const brotli = (text) =>
  brotliCompressSync(Buffer.from(text, 'utf8'), {
    params: {
      [constants.BROTLI_PARAM_QUALITY]: 11,
      [constants.BROTLI_PARAM_SIZE_HINT]: Buffer.byteLength(text),
    },
  }).length;

/** A byte count, grouped and right-aligned, for the size table. */
const fmt = (bytes) => String(bytes.toLocaleString('en-US')).padStart(9);

/** A budget or measurement named in an error message, where padding is noise. */
const plain = (bytes) => bytes.toLocaleString('en-US');

/**
 * Compiles the global sheet the way a production build does, and returns the
 * bytes a browser receives.
 *
 * `apps/web/postcss.config.mjs` is the whole of the project's PostCSS
 * configuration, and because it exists `next build` uses exactly its plugins
 * and nothing else — `@tailwindcss/postcss` — then runs the extracted CSS
 * through the `cssnano-simple` minimizer Next bundles, in production only.
 * Both are resolved from `apps/web` here rather than from this script's own
 * directory, because pnpm only links a package into the app that declares it.
 */
async function compileGlobalSheet() {
  const webRequire = createRequire(join(WEB, 'package.json'));
  const postcss = createRequire(webRequire.resolve('@tailwindcss/postcss'))('postcss');
  const tailwind = webRequire('@tailwindcss/postcss');
  const nextRequire = createRequire(webRequire.resolve('next/package.json'));
  const cssnano = nextRequire('next/dist/compiled/cssnano-simple');
  const source = readFileSync(CSS, 'utf8');
  const compiled = (await postcss([tailwind]).process(source, { from: CSS })).css;
  return (await postcss([cssnano()]).process(compiled, { from: CSS })).css;
}

/*
 * The size of each stylesheet, per scheme — this is the measurement the budget
 * is about, and it is printed on every run so the numbers in a report can be
 * reproduced with one command.
 *
 * The global sheet is measured after compilation and minification because that
 * is what the build ships. A locale sheet is measured as the bytes on disk,
 * because it is served straight out of `public/` by a `<link>` and never passes
 * through PostCSS: that is a deliberate consequence of the mechanism, and it is
 * why a locale sheet must not contain an at-rule.
 */
let compiled = null;
try {
  compiled = await compileGlobalSheet();
} catch (cause) {
  errors.push(
    `the global stylesheet could not be compiled, so its size was not measured: ${cause.message}. ` +
      `The budget is the point of this gate, so this is a failure and not a skip — install the ` +
      `workspace and run it again.`,
  );
}

const globalSheet = compiled === null ? null : {
  raw: Buffer.byteLength(compiled),
  brotli: brotli(compiled),
  // The `@font-face` rules of the shipped sheet, whichever order they ended up
  // in. Summed per rule rather than sliced, so this stays right even if a
  // minifier interleaves them with something else.
  fontBytes: [...compiled.matchAll(/@font-face\s*\{[^}]*\}/g)]
    .reduce((total, rule) => total + Buffer.byteLength(rule[0]), 0),
};

if (globalSheet && globalSheet.raw > GLOBAL_SHEET_BUDGET.rawBytes) {
  errors.push(
    `the global stylesheet compiles to ${plain(globalSheet.raw)} B, over the ` +
      `${plain(GLOBAL_SHEET_BUDGET.rawBytes)} B budget that all ` +
      `${Object.keys(LOCALE_FAMILY).length} locales pay on every page. Rules that only some ` +
      `locales read belong in public/styles/fonts/<locale>.css, not in globals.css.`,
  );
}
if (globalSheet && globalSheet.brotli > GLOBAL_SHEET_BUDGET.brotliBytes) {
  errors.push(
    `the global stylesheet is ${plain(globalSheet.brotli)} B brotli, over the ` +
      `${plain(GLOBAL_SHEET_BUDGET.brotliBytes)} B budget. The defect this budget exists for ` +
      `measured 22.8 kB, paid by every locale including the ten that render none of these glyphs.`,
  );
}
if (globalSheet && globalSheet.fontBytes > GLOBAL_SHEET_BUDGET.fontBytes) {
  errors.push(
    `the @font-face rules in the global stylesheet are ${plain(globalSheet.fontBytes)} B, over the ` +
      `${plain(GLOBAL_SHEET_BUDGET.fontBytes)} B budget. The three majority-script families are ` +
      `12 rules and about 3.6 kB; a family only some locales read belongs in ` +
      `public/styles/fonts/<locale>.css.`,
  );
}

const globalRaw = globalSheet?.raw ?? 0;
const globalBrotli = globalSheet?.brotli ?? 0;

out('');
out(
  `stylesheet budget — the bytes a browser receives, per locale` +
    `\n  ${'locale'.padEnd(8)}${'global raw'.padStart(12)}${'global br'.padStart(11)}` +
    `${'sheet raw'.padStart(12)}${'sheet br'.padStart(11)}${'total raw'.padStart(12)}` +
    `${'total br'.padStart(11)}  sheet`,
);
out(
  `  ${'Latin'.padEnd(8)}${fmt(globalRaw).padStart(3)}${fmt(globalBrotli)}` +
    `${'-'.padStart(12)}${'-'.padStart(11)}${fmt(globalRaw).padStart(3)}${fmt(globalBrotli)}` +
    `  none — the global sheet only`,
);
for (const locale of SCRIPT_LOCALES) {
  const text = sheets.get(`${locale}.css`);
  if (text === null) {
    out(
      `  ${locale.padEnd(8)}${fmt(globalRaw).padStart(3)}${fmt(globalBrotli)}` +
        `${'missing'.padStart(12)}${'missing'.padStart(11)}${'-'.padStart(12)}${'-'.padStart(11)}` +
        `  /styles/fonts/${locale}.css is missing`,
    );
    continue;
  }
  if (/@(?:import|tailwind|apply)\b/.test(strip(text))) {
    errors.push(
      `public/styles/fonts/${locale}.css contains an at-rule, but a sheet served out of public/ is ` +
        `never compiled — the browser would receive it verbatim`,
    );
  }
  const raw = Buffer.byteLength(text);
  const compressed = brotli(text);
  out(
    `  ${locale.padEnd(8)}${fmt(globalRaw).padStart(3)}${fmt(globalBrotli)}` +
      `${fmt(raw)}${fmt(compressed)}${fmt(globalRaw + raw).padStart(3)}${fmt(globalBrotli + compressed)}` +
      `  /styles/fonts/${locale}.css`,
  );
}
out(
  `  ${'budget'.padEnd(8)}${fmt(GLOBAL_SHEET_BUDGET.rawBytes).padStart(3)}` +
    `${fmt(GLOBAL_SHEET_BUDGET.brotliBytes)}  whole sheet; the @font-face rules inside it must ` +
    `stay under ${plain(GLOBAL_SHEET_BUDGET.fontBytes)} B, and a locale sheet adds its own bytes ` +
    `to the one locale that asked for them`,
);
out(
  `  ${'of which'.padEnd(8)}${fmt(globalSheet?.fontBytes ?? 0).padStart(3)}${'-'.padStart(11)}` +
    `  @font-face rules in the global sheet — today 12 rules, one per bundled weight and cut`,
);

if (errors.length > 0) {
  err(`\nfont coverage check failed with ${errors.length} problem(s):`);
  for (const error of errors) err(`  - ${error}`);
  process.exit(1);
}

out(
  `\nfont coverage OK: all ${Object.keys(LOCALE_FAMILY).length} locales are served by a family ` +
    `bundled from this origin, every /fonts/… src resolves to a file that exists, the script ` +
    `families live in per-locale sheets, and the global sheet is inside its budget.`,
);

