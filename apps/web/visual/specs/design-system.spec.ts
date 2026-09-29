import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';

import { KNOWN_A11Y_FINDINGS as KNOWN } from '../known-a11y-findings';

/**
 * Per-story screenshots of the built Storybook, compared against a committed
 * baseline.
 *
 * Why a static build and not a running `storybook dev`: the dev server compiles
 * every story on request, so a capture taken from it measures the machine as much
 * as the design, and every run needs a live Node process for its whole duration.
 * A static build is what a reviewer would actually deploy, and it is what CI can
 * produce without a Storybook server.
 *
 * Chromatic and Loki are both hosted and both need a token this environment does
 * not have, so neither is wired up and neither is claimed. What this gives is the
 * half that can run offline: a real pixel comparison, in `pnpm test:visual`,
 * failing the build when a component's rendering changes and no one said so.
 * What a hosted service would add is the review UI and cross-branch diffing;
 * swapping this file for `@storybook/addon-chromatic` is a config change once
 * `CHROMATIC_PROJECT_TOKEN` exists, and the screenshots this produces are the
 * artefacts it would upload.
 *
 * Run:
 *   pnpm build-storybook
 *   pnpm test:visual              # compare against __screenshots__/
 *   pnpm test:visual:update       # accept the current rendering as the baseline
 */

const APP = resolve(import.meta.dirname, '..', '..');
const HERE = resolve(import.meta.dirname, '..');
const INDEX = resolve(APP, 'storybook-static', 'index.json');

/**
 * Findings collected across the run.
 *
 * The tests run in parallel and the workers are separate processes, so each one
 * appends its own findings to a JSONL sidecar and the final test reads the whole
 * file back. That is not a detail: a module-level array in a parallel run keeps
 * one worker's findings and discards the rest, and the gate would then pass on
 * whatever that one happened to see.
 */
const REPORT_LINES = resolve(HERE, 'a11y-report.jsonl');

function record(...findings: Finding[]) {
  if (findings.length === 0) return;
  // Cleared at the start of the *run*, not the process, so a partial run does not
  // inherit the last one's findings. `test.beforeAll` on the describe does this
  // only in the worker that owns it, so the truncation happens once at import.
  appendFileSync(
    REPORT_LINES,
    `${findings.map((finding) => JSON.stringify(finding)).join('\n')}\n`,
  );
}

function drain(): Finding[] {
  if (!existsSync(REPORT_LINES)) return [];
  const merged = new Map<string, Finding>();
  for (const line of readFileSync(REPORT_LINES, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const finding = JSON.parse(line) as Finding;
      merged.set(keyOf(finding), finding);
    } catch {
      // A half-written line from a killed worker is not a finding.
    }
  }
  return [...merged.values()];
}

interface Finding {
  story: string;
  rule: string;
  impact: string | null | undefined;
  detail: string;
  target: string;
}

/** One story id as Storybook writes it in `index.json`. */
interface IndexEntry {
  id: string;
  title: string;
  name: string;
  tags: string[];
}

/**
 * The locale and scheme matrix, applied to a small hand-picked set rather than to
 * everything. Every story is captured once in the platform default; multiplying
 * ~110 stories by four locale/scheme combinations would be a baseline nobody
 * keeps current. These four are the frames where the differences are largest and
 * where a regression is most likely to be invisible: a mirrored layout, a
 * swapped palette, a non-Latin script, and a Nastaliq line height.
 */
const MATRIX = [
  { id: 'primitives-button--variants', locale: 'fa', scheme: 'dark' },
  { id: 'primitives-button--sizes', locale: 'fa', scheme: 'light' },
  { id: 'data-stat--with-provenance', locale: 'fa', scheme: 'dark' },
  { id: 'forms-input--in-persian', locale: 'fa', scheme: 'light' },
  { id: 'forms-switch--default', locale: 'fa', scheme: 'dark' },
  { id: 'navigation-tabs--in-persian', locale: 'en', scheme: 'dark' },
  { id: 'navigation-navigation--pagination-in-rtl', locale: 'fa', scheme: 'light' },
  { id: 'overlays-dialog--in-persian', locale: 'fa', scheme: 'dark' },
  { id: 'data-datatable--alignment-in-rtl', locale: 'fa', scheme: 'light' },
  { id: 'surfaces-shapeview--in-persian', locale: 'fa', scheme: 'dark' },
  { id: 'overlays-toast--variants', locale: 'en', scheme: 'dark' },
  { id: 'overlays-commandpalette--in-persian', locale: 'fa', scheme: 'light' },
];

function readIndex(): IndexEntry[] {
  if (!existsSync(INDEX)) {
    throw new Error(
      `No Storybook build at ${INDEX}. Run "pnpm build-storybook" before "pnpm test:visual".`,
    );
  }
  const parsed = JSON.parse(readFileSync(INDEX, 'utf8')) as {
    entries?: Record<string, IndexEntry>;
    v?: number;
    stories?: IndexEntry[];
  };
  const entries = parsed.stories ?? Object.values(parsed.entries ?? {});
  const usable = entries.filter((entry) => !entry.tags?.includes('stories-missing'));
  if (usable.length === 0) throw new Error(`${INDEX} contains no stories.`);
  return usable.sort((a, b) => a.id.localeCompare(b.id));
}

const ENTRIES = readIndex();
const byId = new Map(ENTRIES.map((entry) => [entry.id, entry]));

/**
 * A capture is only comparable if the frame is identical every time, so the page
 * is put into a fixed state before the shutter: the document attributes the
 * toolbar would have set, a settled font stack, and no caret.
 *
 * The wait is on Storybook's own render events rather than on a selector, for two
 * reasons that both bit during development. A `<style>` element has no bounding
 * box, so `Button` — which injects its keyframes as its first child — never
 * satisfies a visibility wait. And `Dialog`, `CommandPalette` and
 * `OfflineBanner` portal into `document.body`, so `#storybook-root` is empty and
 * there is nothing inside the canvas to wait for at all.
 */
async function openStory(page: Page, id: string, locale: string, scheme: string) {
  await page.addInitScript(() => {
    // `null` is inferred as `null` from the literal, so the type is stated:
    // without it `state.finished = 'error'` below is an error and the whole
    // init script fails to compile into the page.
    const state: {
      rendered: boolean;
      thrown: string;
      errored: string;
      missing: boolean;
      finished: string | null;
    } = { rendered: false, thrown: '', errored: '', missing: false, finished: null };
    (globalThis as unknown as { __ecoStory: typeof state }).__ecoStory = state;

    // Storybook 9 emits its render events on the preview channel, not on
    // `document`, so the channel is what has to be subscribed to — and it does
    // not exist when the init script runs, hence the poll.
    const attach = () => {
      const channel = (
        globalThis as unknown as {
          __STORYBOOK_ADDONS_CHANNEL__?: {
            on: (event: string, handler: (payload: never) => void) => void;
          };
        }
      ).__STORYBOOK_ADDONS_CHANNEL__;
      if (!channel) {
        setTimeout(attach, 0);
        return;
      }
      channel.on('storyRendered', (() => {
        state.rendered = true;
      }) as (payload: never) => void);
      channel.on('storyThrownException', ((payload: { message?: string }) => {
        state.thrown = payload?.message ?? 'unknown';
        state.rendered = true;
      }) as (payload: never) => void);
      channel.on('storyErrored', (() => {
        state.errored = 'the story reported an error';
        state.rendered = true;
      }) as (payload: never) => void);
      channel.on('storyMissing', (() => {
        state.missing = true;
        state.rendered = true;
      }) as (payload: never) => void);
      channel.on('storyFinished', ((payload: { status?: string }) => {
        state.finished = payload?.status ?? 'unknown';
      }) as (payload: never) => void);
    };
    attach();
  });

  const url = `/iframe.html?id=${encodeURIComponent(id)}&viewMode=story&globals=${encodeURIComponent(
    `locale:${locale};scheme:${scheme}`,
  )}`;
  await page.goto(url);
  await page.waitForFunction(
    () => {
      const state = (globalThis as unknown as { __ecoStory?: { rendered: boolean } }).__ecoStory;
      return state?.rendered === true;
    },
    undefined,
    { timeout: 30000 },
  );
  await page.evaluate(() => document.fonts.ready);

  const failure = await page.evaluate(() => {
    const state = (
      globalThis as unknown as {
        __ecoStory: { missing: boolean; thrown: string; errored: string };
      }
    ).__ecoStory;
    if (state.missing) return 'the story id is not in the built Storybook';
    if (state.thrown) return `the story threw: ${state.thrown}`;
    if (state.errored) return state.errored;
    return null;
  });
  if (failure) throw new Error(`${id}: ${failure}`);
}

/**
 * axe rules switched off for a story canvas, and why.
 *
 * A story is a component, not a document. It has no `<main>`, no `<h1>` and no
 * landmark structure, because a component library is not responsible for the page
 * around it — so those four rules fail on every single story and say nothing about
 * any component. Turning them off is scoping the tool to the thing being tested.
 *
 * `color-contrast` is deliberately *not* in this list. A design system whose whole
 * claim is a token palette is exactly where a contrast regression must fail, and
 * the gate has to be able to see it.
 */
const AXE_RULES = [
  'region',
  'landmark-one-main',
  'landmark-unique',
  'page-has-heading-one',
  'bypass',
] as const;

/**
 * The accessibility audit, ratcheted rather than absolute.
 *
 * axe-core runs over every story, and every violation is written to
 * `visual/a11y-report.json`. A run fails on the violations that are *not* in the
 * committed `visual/known-a11y-findings.json` — so a new defect fails, and a
 * defect that has been fixed fails nothing even though the list still names it.
 *
 * The alternative, asserting zero violations, is what made this unusable: the
 * first run produced 21 failures across six distinct defects, and a wall of 21
 * red tests is a wall nobody reads, so the gate gets switched off and the two
 * genuine regressions hiding inside it go with it. A ratchet keeps the whole
 * audit reporting, keeps every finding named in a file that says what it is, and
 * makes "no new ones" the only thing that can break the build.
 *
 * Clearing a finding means editing `known-a11y-findings.json` — a file whose only
 * content is explanations — which is a deliberate act rather than a side effect
 * of running the tests.
 */
async function auditStory(page: Page, storyId: string) {
  // `disableRules` rather than a `rules: [{ enabled: false }]` config: those two
  // axe options have different shapes and only one of them is accepted here.
  const results = await new AxeBuilder({ page }).disableRules([...AXE_RULES]).analyze();
  return results.violations.flatMap((violation) =>
    // Every node, not the first three: a finding is a component-level problem and
    // three of its cells is not the same finding as one of them.
    violation.nodes.map((node) => ({
      story: storyId,
      rule: violation.id,
      impact: violation.impact,
      // axe's own numbers rather than a re-derivation: for `color-contrast` it
      // carries the measured ratio, the two colours it measured and the ratio the
      // size and weight of the text required. Without those three, "a contrast
      // failure" is a sentence nobody can act on.
      ...measured(node),
      target: node.target.join(' '),
    })),
  );
}

function measured(node: { any?: unknown[]; all?: unknown[]; none?: unknown[] }) {
  const checks = [...(node.any ?? []), ...(node.all ?? []), ...(node.none ?? [])] as {
    data?: Record<string, unknown>;
  }[];
  const data = checks.map((check) => check.data ?? {}).find((entry) => 'contrastRatio' in entry);
  if (!data) return { detail: '' };
  return {
    detail: `${String(data.fgColor)} on ${String(data.bgColor)} = ${String(data.contrastRatio)}:1, needs ${String(
      data.expectedContrastRatio,
    )} at ${String(data.fontSize)} ${String(data.fontWeight)}`,
  };
}

/** A finding is identified by where it is and what it is, not by its numbers. */
function keyOf(finding: { story: string; rule: string; target: string }) {
  return `${finding.story} | ${finding.rule} | ${finding.target}`;
}

const SHOT = {
  fullPage: true,
  animations: 'disabled' as const,
  caret: 'hide' as const,
  // 0.2 per-channel JND, and 0.2% of pixels before a run is failed. Tighter than
  // the Playwright default so a one-colour regression in a badge is a failure and
  // not a rounding difference in an anti-aliased glyph.
  threshold: 0.2,
  maxDiffPixelRatio: 0.002,
};

test.describe('design system', () => {
  test('the preview renders the production tokens, not a Storybook approximation', async ({
    page,
  }) => {
    // The failure this guards against is silent, and it is the reason a design
    // system catalogue is worth anything. If the Tailwind pipeline or the
    // stylesheet import breaks, every story still renders, every screenshot still
    // matches a baseline of unstyled text, and nothing anywhere reports a
    // problem. So the tokens are asserted, not assumed: a resolved colour, a
    // spacing step, a radius, the bundled font, and the dark half of the
    // `light-dark()` pair.
    await openStory(page, 'primitives-button--default', 'en', 'light');

    const light = await page.evaluate(() => {
      const root = document.documentElement;
      const button = document.querySelector<HTMLElement>('#storybook-root button');
      if (!button) throw new Error('no button in the story canvas');
      const style = getComputedStyle(button);
      return {
        lang: root.lang,
        dir: root.dir,
        canvas: getComputedStyle(document.body).backgroundColor,
        action: style.backgroundColor,
        padding: style.padding,
        radius: style.borderRadius,
        fontFamily: style.fontFamily,
        themeSurface: getComputedStyle(root).getPropertyValue('--surface').trim(),
      };
    });

    // The document carries the locale and the direction the toolbar asked for.
    expect(light.lang).toBe('en');
    expect(light.dir).toBe('ltr');
    // `body` is styled by `globals.css`, so a resolved `oklch()` here is proof the
    // production stylesheet reached the preview and the tokens resolved.
    expect(light.canvas).toMatch(/^oklch\(/);
    // `--surface` is only ever declared in `globals.css`.
    expect(light.themeSurface).toContain('light-dark(');
    // `--space-3` / `--space-4` on the default size. A Tailwind build that did
    // not run would leave these at the browser's default button padding.
    expect(light.padding).toBe('12px 16px');
    expect(light.radius).toBe('8px');
    expect(light.fontFamily).toMatch(/Vazirmatn/);

    const fonts = await page.evaluate(() =>
      [...document.fonts].map((face) => `${face.family} ${face.status}`),
    );
    // One of the families that only exists in this repository is `JetBrains
    // Mono`; if the stylesheet had not been applied, no such face would be known.
    expect(fonts.some((face) => face.startsWith('JetBrains Mono'))).toBe(true);

    // The dark half is a different question from the light one: `light-dark()`
    // resolves against the used colour scheme, so the toolbar has to be setting
    // `color-scheme` on the document rather than toggling a class.
    await openStory(page, 'primitives-button--default', 'en', 'dark');
    const darkCanvas = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(darkCanvas).toMatch(/^oklch\(/);
    expect(darkCanvas).not.toBe(light.canvas);
  });

  test('the seven bundled families are served from this origin', async ({ page }) => {
    const requested: string[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/fonts/')) requested.push(request.url());
    });
    await openStory(page, 'primitives-button--sizes', 'fa', 'light');
    // A Latin label will not fetch the Arabic cut, so force one: a frame with no
    // Vazirmatn Arabic request is a frame measured with fallback metrics.
    await page.evaluate(() => document.body.append('متن'));
    await page.evaluate(() => document.fonts.ready);
    expect(requested.some((url) => url.includes('vazirmatn-arabic'))).toBe(true);
    // No third-party font request, which is the "zero external font requests"
    // claim in the stylesheet header.
    expect(requested.every((url) => url.startsWith('http://localhost'))).toBe(true);
  });

  for (const entry of ENTRIES) {
    test(`${entry.id}`, async ({ page }) => {
      await openStory(page, entry.id, 'fa', 'light');
      // The page, not `#storybook-root`: three of these components portal into
      // `document.body`, and a locator screenshot of an empty root would be a
      // baseline of a blank frame that any later change would happily match.
      await expect(page).toHaveScreenshot(`${entry.id}.png`, SHOT);
      record(...(await auditStory(page, entry.id)));
    });
  }

  for (const { id, locale, scheme } of MATRIX) {
    test(`${id} — ${locale} / ${scheme}`, async ({ page }) => {
      // Named up front rather than skipped silently: a matrix entry pointing at a
      // renamed story should fail, not quietly photograph nothing.
      expect(byId.has(id), `${id} is in the matrix but not in the built Storybook`).toBe(true);
      await openStory(page, id, locale, scheme);
      await expect(page).toHaveScreenshot(`${id}__${locale}-${scheme}.png`, SHOT);
      record(...(await auditStory(page, `${id} (${locale} / ${scheme})`)));
    });
  }

  /**
   * The audit is a single test rather than a per-story assertion, so that a run
   * with known findings still passes and the report is written once, from one
   * place, instead of once per worker.
   */
  test('no new accessibility findings', async () => {
    const found = drain();
    const known = new Map<string, string>(KNOWN.map((finding) => [keyOf(finding), finding.note]));

    // Zero observations is not a clean bill of health. If the story tests were
    // filtered out, a worker died, or the report file was deleted, an empty
    // result is otherwise indistinguishable from "nothing is wrong" — and that is
    // the one thing an audit must never be able to conclude by accident.
    expect(
      found.length,
      'no accessibility findings were recorded, so nothing was audited: the story tests did not run, or their workers died before writing the report.',
    ).not.toBe(0);

    const newFindings = found.filter((finding) => !known.has(keyOf(finding)));
    const cleared = [...known.keys()].filter(
      (key) => !found.some((finding) => keyOf(finding) === key),
    );

    // Written every run, whether or not it passed, so the file is the audit of
    // record rather than a log of the last failure.
    mkdirSync(HERE, { recursive: true });
    writeFileSync(
      resolve(HERE, 'a11y-report.json'),
      `${JSON.stringify(
        {
          stories: ENTRIES.length + MATRIX.length,
          known: found.filter((finding) => known.has(keyOf(finding))).length,
          new: newFindings.length,
          cleared,
          findings: found.map((finding) => ({ ...finding, known: known.has(keyOf(finding)) })),
        },
        null,
        2,
      )}\n`,
    );

    if (cleared.length > 0) {
      console.log(
        `\n${cleared.length} finding(s) no longer reproduce — remove them from known-a11y-findings.json:\n${cleared
          .map((key) => `  ${key}`)
          .join('\n')}`,
      );
    }
    expect(
      newFindings,
      `new accessibility findings — ${newFindings.length}. They are not in visual/known-a11y-findings.json, so this is new breakage. The full audit is in visual/a11y-report.json.`,
    ).toEqual([]);
  });
});
