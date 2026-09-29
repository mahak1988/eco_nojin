import { execFileSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

/**
 * Proves the locale gates can actually see the failures they exist to catch.
 *
 * A gate that has never been observed failing is a gate of unknown correctness.
 * `check-locale-encoding.mjs` was written to catch seven byte-identical mojibake
 * catalogs, and reported "OK" on the day it was written because the code had
 * already been fixed. That is the same class of error as claiming a theme was
 * missing without reading the stylesheet: concluding a defect is absent without
 * testing the detector.
 *
 * So each gate runs here against a deliberately corrupted copy of the real
 * catalogues and is required to fail, with a message that names the problem.
 * The mojibake below is verbatim from `git show HEAD:apps/web/messages/ru.json`
 * — the string seven locales actually shipped.
 */

/**
 * Locate the repository root by walking up until a known gate script is found,
 * rather than counting `..` segments. Counting is what made the first two drafts
 * of this file point at `apps/apps/web` and `apps/scripts`; a walk cannot be off
 * by one, and it fails loudly if the layout changes.
 */
function findRepoRoot(from: string): string {
  let current = from;
  for (let depth = 0; depth < 10; depth += 1) {
    if (existsSync(join(current, 'scripts', 'check-locale-encoding.mjs'))) return current;
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`could not locate the repository root above ${from}`);
}

const WEB_ROOT = join(findRepoRoot(import.meta.dirname), 'apps', 'web');
const REPO_ROOT = findRepoRoot(import.meta.dirname);
const ENCODING_GATE = join(REPO_ROOT, 'scripts', 'check-locale-encoding.mjs');
const PAGE_META_GATE = join(REPO_ROOT, 'scripts', 'check-page-meta.mjs');
const FONT_GATE = join(REPO_ROOT, 'scripts', 'check-font-coverage.mjs');
const MESSAGES = join(WEB_ROOT, 'messages');
/** Verbatim from the shipped `ru.json`, i.e. what seven locales actually contained. */
const MOJIBAKE = {
  name: 'ظ‡غŒط¯ط±ظˆظ…ط§ ظ†ظˆعکغŒظ†',
  description:
    'ط¨ط®ط´ ط¹ظ„ظ…غŒ ط§ع©ظˆ ظ†ظˆعکغŒظ†ط› ظ‡ظ…ط±ط§ظ‡غŒ ط¨ط±ط§غŒ ظپظ‡ظ… ط¨ظ‡طھط± ط¢ط¨طŒ ط®ط§ع©طŒ ظ¾طˆط´ط´ ع¯غŒط§ظ‡غŒ ظˆ ط§ظ‚ظ„غŒظ…',
};

let scratch: string;

/**
 * Every test in this file copies the whole `messages/` directory and spawns a
 * Node process per gate run. A single test here therefore costs three copies of
 * fourteen catalogues plus three interpreter starts, which clears vitest's 5s
 * default under load and fails as a timeout that reads like a broken detector.
 * The assertion is the exit code, not the clock, so the clock gets real headroom.
 */
const GATE_TIMEOUT_MS = 60_000;

const run = (script: string, env: Record<string, string> = {}) => {
  try {
    const stdout = execFileSync(process.execPath, [script], {
      encoding: 'utf8',
      env: { ...process.env, ...env },
    });
    return { code: 0, stdout, stderr: '' };
  } catch (error) {
    const failure = error as { status?: number; stdout?: string; stderr?: string };
    return {
      code: failure.status ?? 1,
      stdout: failure.stdout ?? '',
      stderr: failure.stderr ?? '',
    };
  }
};

/** Reset the scratch directory to an exact copy of the real catalogues. */
const resetScratch = () => {
  rmSync(scratch, { recursive: true, force: true });
  cpSync(MESSAGES, scratch, { recursive: true });
};

const readScratch = (locale: string) =>
  JSON.parse(readFileSync(join(scratch, `${locale}.json`), 'utf8'));
const writeScratch = (locale: string, value: unknown) =>
  writeFileSync(join(scratch, `${locale}.json`), JSON.stringify(value, null, 2), 'utf8');

beforeAll(() => {
  scratch = mkdtempSync(join(tmpdir(), 'eco-locale-gate-'));
  resetScratch();
});

afterAll(() => {
  rmSync(scratch, { recursive: true, force: true });
});

describe('check-locale-encoding is a working detector', () => {
  it(
    'passes on the real catalogues',
    () => {
      resetScratch();
      const result = run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch });
      expect(result.code, result.stdout + result.stderr).toBe(0);
    },
    GATE_TIMEOUT_MS,
  );

  it(
    'fails on the exact mojibake that shipped in seven locales',
    () => {
      resetScratch();
      for (const locale of ['bn', 'hi', 'it', 'ms', 'pt', 'ru', 'zh']) {
        const catalogue = readScratch(locale);
        catalogue.brand.name = MOJIBAKE.name;
        catalogue.brand.description = MOJIBAKE.description;
        writeScratch(locale, catalogue);
      }

      const result = run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch });
      expect(result.code, 'the gate passed on seven mojibake catalogs').not.toBe(0);
      const output = result.stdout + result.stderr;
      expect(output).toContain('mojibake');
      // Every corrupted locale must be named, not just the first.
      for (const locale of ['bn', 'hi', 'it', 'ms', 'pt', 'ru', 'zh']) {
        expect(output, `the gate did not name ${locale}`).toContain(`${locale}:`);
      }
    },
    GATE_TIMEOUT_MS,
  );

  it(
    'fails on a catalog that is wholesale untranslated',
    () => {
      // The other half of the gate: readable text that is not in the locale's
      // language. Russian filled with English is not mojibake, but it is just as
      // wrong, and the first version of the file would have passed it.
      //
      // The scope is a whole catalog, not a stray string: the detector measures the
      // share of letters in the right script, so one foreign string in an otherwise
      // Russian catalog is correctly ignored. Replacing the file wholesale is the
      // failure mode that actually shipped — seven catalogs were byte-identical
      // copies of one broken file.
      resetScratch();
      const catalogue = readScratch('ru');
      catalogue.brand.name = 'Hydroma Nojin';
      writeScratch('ru', catalogue);

      const single = run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch });
      expect(
        single.code,
        'one foreign string in a translated catalog should not fail a ratio check',
      ).toBe(0);

      resetScratch();
      const english = readScratch('en');
      writeScratch('ru', english);
      const result = run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch });
      expect(result.code, 'the gate passed an English copy filed as Russian').not.toBe(0);
      const output = result.stdout + result.stderr;
      expect(output).toContain('own script');
      expect(output, 'the gate did not name the offending locale').toContain('ru:');
    },
    GATE_TIMEOUT_MS,
  );

  it(
    'does not flag correct Persian, Arabic or Urdu',
    () => {
      // The regression guard for the range bug. The first version of the browser
      // rule was `/[ط-٩]/`, which looks like the mojibake glyphs but is a range
      // spanning every ordinary Arabic letter, so it fired on correct Persian.
      resetScratch();
      for (const locale of ['fa', 'ar', 'ur']) {
        const catalogue = readScratch(locale);
        catalogue.brand.name = MOJIBAKE.name;
        writeScratch(locale, catalogue);
      }
      const result = run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch });
      expect(result.code, 'correct RTL text was misread as corrupt').not.toBe(0);

      // Now prove the detection rule itself leaves correct text alone.
      resetScratch();
      for (const locale of ['fa', 'ar', 'ur']) {
        const correct = readScratch(locale);
        expect(correct.brand.name, `${locale} has an empty brand name`).toBeTruthy();
      }
      expect(run(ENCODING_GATE, { ECO_MESSAGES_DIR: scratch }).code).toBe(0);
    },
    GATE_TIMEOUT_MS,
  );
});

describe('check-page-meta is a working detector', () => {
  it(
    'passes on the real tree',
    () => {
      const result = run(PAGE_META_GATE);
      expect(result.code, result.stdout + result.stderr).toBe(0);
    },
    GATE_TIMEOUT_MS,
  );

  it(
    'matches every shape of the pattern that existed',
    () => {
      // Three spellings shipped across the 53 pages, plus the two-locale hreflang
      // map on 66 files. A rewrite of the gate must keep matching all of them.
      const source = readFileSync(PAGE_META_GATE, 'utf8');
      for (const shape of ['TITLES', 'DESCRIPTIONS', 'titles', 'descriptions']) {
        expect(source, `the gate no longer names ${shape}`).toContain(shape);
      }
      expect(source).toContain('languages:');
      expect(source).toContain('pageMeta');
    },
    GATE_TIMEOUT_MS,
  );
});

describe('check-font-coverage is a working detector', () => {
  it(
    'passes on the real stylesheet',
    () => {
      const result = run(FONT_GATE);
      expect(result.code, result.stdout + result.stderr).toBe(0);
    },
    GATE_TIMEOUT_MS,
  );

  it(
    'fails when a locale has a font stack but nothing applies it',
    () => {
      // The bug this gate was written for. `--font-sans-deva` was declared for
      // Devanagari but no `html[lang="hi"]` rule ever selected it, so the stack
      // did nothing. The gate caught that on its first run, after I had written the
      // tokens and forgotten the selector.
      const css = readFileSync(join(WEB_ROOT, 'src', 'app', 'globals.css'), 'utf8');
      const doctored = css.replace(/html\[lang="hi"\]/g, 'html[data-locale="hi"]');
      expect(doctored, 'the hi selector was not found to begin with').not.toBe(css);

      const path = join(scratch, 'doctored.css');
      writeFileSync(path, doctored, 'utf8');

      const result = run(FONT_GATE, { ECO_CSS_FILE: path });
      expect(result.code, 'the gate passed a declared-but-unapplied font stack').not.toBe(0);
      const output = result.stdout + result.stderr;
      expect(output).toContain('hi');
      expect(output).toContain('is never applied');
    },
    GATE_TIMEOUT_MS,
  );
});
