#!/usr/bin/env node
/**
 * Core Web Vitals gate.
 *
 * The master plan makes performance binding in two places — §3.2 states a budget
 * and §8 lists "کارایی | بودجهٔ §۳٫۲" as a non-functional standard — and for the
 * whole life of this repository no gate measured it. `pnpm quality` ran lint,
 * types, tests, i18n, site-url and tokens. It never loaded a page. Every number in
 * §3.2 was a build-time number, which is a different claim: it says how big the
 * bundle is, not whether the page is fast.
 *
 * This gate loads real pages from a real production build and measures them.
 *
 * ── What the previous version of this file got wrong ────────────────────────
 *
 * It was present, tracked in `package.json` as `test:cwv`, and had never
 * succeeded. Three separate defects, in order of severity:
 *
 *   1. It could not fail on a budget miss even if Lighthouse had run. The
 *      assertions lived in `lighthouserc.json`, an LHCI config, and the script
 *      invoked the `lighthouse` CLI, which does not read LHCI configs and whose
 *      exit code is 0 whenever it produced a report regardless of the scores in
 *      it. The script then printed "CWV budgets met". That is a check that
 *      reports success unconditionally.
 *   2. `npx --no-install lighthouse --config-path <lhci.json>` is not a
 *      lighthouse invocation. `--config-path` takes a Lighthouse *user* config
 *      (chromeFlags, extends, settings); an LHCI `ci` block is not one, and the
 *      CLI was given no URL to audit.
 *   3. It required a server the author had to start by hand, and it was not in
 *      the `quality` chain, so nothing ever started it.
 *
 * This is the "written and never enabled" defect and the "does not work" defect
 * at once. It is replaced rather than repaired: there is no part of the old file
 * worth keeping, and repairing it in place would have left the same structure
 * with the same failure mode.
 *
 * ── The rule this file is most careful about ────────────────────────────────
 *
 * A gate that passes because it ran nothing is a defect, and this repository has
 * found that defect before — in token references, in colour utilities, in
 * contrast. So every one of these is a FAILURE, never a pass:
 *
 *   - the `lighthouse` package is not resolvable;
 *   - no Chrome could be launched;
 *   - the base URL does not answer;
 *   - a route returned a status the measurement cannot trust (the gate reads the
 *     expected status from the route list, so a route that starts answering 500
 *     fails the gate instead of quietly reporting a fast error page);
 *   - fewer runs completed than `runs.cold` / `runs.warm` ask for, because a
 *     p75 over two samples is not a p75;
 *   - the report JSON has no value for a metric the budget covers.
 *
 * `exit 2` is reserved for "could not measure". `exit 1` is "measured, and missed
 * the budget". A caller can tell the two apart, which matters more than the
 * single non-zero code: a machine cannot repair a regression, and a machine can
 * act on "I have no idea what the state is".
 *
 * ── INP ─────────────────────────────────────────────────────────────────────
 *
 * INP is not asserted. It is a field metric; no lab run produces it. What is
 * asserted in its place is Total Blocking Time, Lighthouse's lab proxy, against
 * a budget that is named `tbtProxyBudgetMs` in the config and printed as a proxy
 * everywhere it appears. Calling TBT "INP" would be the exact fabrication this
 * repository keeps catching.
 *
 * ── Cold and warm ───────────────────────────────────────────────────────────
 *
 * Both are measured, in one Chrome instance on one page. The first navigation is
 * cold (empty HTTP cache); the following navigations to the same route are warm
 * (cache populated). They are reported separately and gated separately. A repeat
 * visit is a different product from a first visit and a gate that only ever sees
 * the warm number describes the wrong one.
 */
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB_ROOT = join(REPO_ROOT, 'apps', 'web');
const DOCS = join(REPO_ROOT, 'docs', 'performance');
// CWV_CONFIG exists so the gate can be pointed at a scratch config — one route,
// one budget — when testing the gate itself. The committed default is the only
// one that decides anything.
const CONFIG_PATH = process.env.CWV_CONFIG
  ? process.env.CWV_CONFIG.replace('{REPO_ROOT}', REPO_ROOT)
  : join(DOCS, 'cwv-budgets.json');
const RESULTS_DIR = process.env.CWV_RESULTS_DIR
  ? process.env.CWV_RESULTS_DIR.replace('{REPO_ROOT}', REPO_ROOT)
  : join(DOCS, 'results');
const BASELINE_PATH = join(RESULTS_DIR, 'baseline.json');

const argv = process.argv.slice(2);
const COLLECT_ONLY = argv.includes('--collect');
const RUNS_OVERRIDE = (() => {
  const i = argv.indexOf('--runs');
  return i === -1 ? null : Number(argv[i + 1]);
})();

const BASE_URL = (process.env.CWV_BASE_URL ?? 'http://localhost:3107').replace(/\/$/, '');

/** Exit codes. 2 means the gate did not measure; it never means "fine". */
const EXIT_BUDGET = 1;
const EXIT_UNMEASURABLE = 2;

/** How many times one navigation may be re-run when it produced no metrics at all. */
const MAX_RUN_RETRIES = 2;

function unmeasurable(lines) {
  console.error('\nCWV gate could not measure. This is a failure, not a pass.\n');
  for (const line of lines) console.error(`  ${line}`);
  console.error('');
  process.exit(EXIT_UNMEASURABLE);
}

// ── configuration ────────────────────────────────────────────────────────────

if (!existsSync(CONFIG_PATH)) unmeasurable([`no config at ${CONFIG_PATH}`]);
let CFG;
try {
  // Strip a UTF-8 BOM. Editors and PowerShell's `Set-Content -Encoding utf8` add
  // one, and `JSON.parse` rejects it, which would turn a budget edit into a
  // mysterious "could not measure".
  CFG = JSON.parse(readFileSync(CONFIG_PATH, 'utf8').replace(/^﻿/, ''));
} catch (error) {
  unmeasurable([`config is not valid JSON: ${error.message}`]);
}
if (!Array.isArray(CFG.routes) || CFG.routes.length === 0) unmeasurable(['config lists no routes']);
if (!CFG.budgets) unmeasurable(['config has no budgets block']);

const RUNS = {
  cold: RUNS_OVERRIDE ?? CFG.runs?.cold ?? 5,
  warm: RUNS_OVERRIDE ?? CFG.runs?.warm ?? 3,
};

// ── dependencies ─────────────────────────────────────────────────────────────

let lighthouse;
let chromeLauncher;
let puppeteer;
try {
  const req = createRequire(join(WEB_ROOT, 'package.json'));
  const lhEntry = req.resolve('lighthouse');
  // chrome-launcher and puppeteer-core are lighthouse's own dependencies, not
  // apps/web's, so they resolve from beside lighthouse and not from the app.
  const lhDir = dirname(lhEntry);
  req.resolve('chrome-launcher', { paths: [lhDir] });
  req.resolve('puppeteer-core', { paths: [lhDir] });
  lighthouse = (await import(urlOf(lhEntry))).default;
  chromeLauncher = await import(urlOf(req.resolve('chrome-launcher', { paths: [lhDir] })));
  puppeteer = (await import(urlOf(req.resolve('puppeteer-core', { paths: [lhDir] })))).default;
} catch (error) {
  unmeasurable([
    'the `lighthouse` package is not resolvable from apps/web.',
    `  ${error.message.split('\n')[0]}`,
    '  add it:  pnpm -C apps/web add -D lighthouse@^13.5.0',
  ]);
}
function urlOf(p) {
  return 'file:///' + p.replace(/\\/g, '/');
}

// ── is anything actually serving? ────────────────────────────────────────────

const probe = spawnSync(
  process.execPath,
  [
    '-e',
    `fetch(${JSON.stringify(BASE_URL + '/health')}).then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))`,
  ],
  { stdio: 'ignore' },
);
if (probe.status !== 0) {
  unmeasurable([
    `nothing is answering at ${BASE_URL}.`,
    '  this gate measures a *production* build; it will not start one for you,',
    '  because a build left running is a build nobody stops. Start one with:',
    '    pnpm -C apps/web build && pnpm -C apps/web start -- -p 3107',
    '  then point CWV_BASE_URL elsewhere if you used a different port.',
  ]);
}

// ── measurement ──────────────────────────────────────────────────────────────

const LIGHTHOUSE_FLAGS = {
  formFactor: CFG.throttling?.formFactor ?? 'desktop',
  screenEmulation: CFG.throttling?.screenEmulation ?? false,
  throttlingMethod: CFG.throttling?.throttlingMethod ?? 'simulate',
  throttling: CFG.throttling?.throttling,
  channel: 'cli',
  output: 'json',
  logLevel: 'error',
};

function quantiles(values) {
  const s = [...values].sort((a, b) => a - b);
  const at = (q) => {
    if (s.length === 0) return null;
    // nearest-rank: the smallest value at or above the q-th position
    const rank = Math.ceil(q * s.length);
    return s[Math.min(s.length - 1, Math.max(0, rank - 1))];
  };
  return { n: s.length, median: at(0.5), p75: at(0.75), min: s[0], max: s[s.length - 1] };
}

const num = (lhr, id) => {
  const v = lhr?.audits?.[id]?.numericValue;
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
};

/** The LCP phase breakdown, which is the only place the "why" is recorded. */
function lcpBreakdown(lhr) {
  const items = lhr?.audits?.['lcp-breakdown-insight']?.details?.items ?? [];
  const phases = items.find((i) => i?.type === 'table')?.items ?? [];
  const node = items.find((i) => i?.type === 'node');
  return {
    phases: phases.map((p) => ({ subpart: p.subpart, ms: p.duration })),
    element: node?.snippet ?? null,
    elementLabel: node?.nodeLabel ?? null,
    note: 'phase durations come from the unthrottled trace; the headline LCP is the simulated value, so the phases do not sum to it',
  };
}

function transfer(lhr) {
  const reqs = lhr?.audits?.['network-requests']?.details?.items ?? [];
  const sum = (pred) =>
    reqs.filter(pred).reduce((a, r) => a + (typeof r.transferSize === 'number' ? r.transferSize : 0), 0);
  return {
    totalBytes: num(lhr, 'total-byte-weight') ?? sum(() => true),
    requestCount: reqs.length,
    javascriptBytes: sum((r) => r.resourceType === 'Script'),
    cssBytes: sum((r) => r.resourceType === 'Stylesheet'),
    fontBytes: sum((r) => r.resourceType === 'Font'),
    documentBytes: sum((r) => r.resourceType === 'Document'),
    fontUrls: [...new Set(reqs.filter((r) => r.resourceType === 'Font').map((r) => r.url))],
    fontsWithLongCache: num(lhr, 'uses-long-cache-ttl') ?? null,
  };
}

/** Response headers for the font files, read straight off the running server. */
async function fontHeaders(urls) {
  const out = [];
  for (const url of urls.slice(0, 12)) {
    try {
      const res = await fetch(url, { method: 'HEAD' });
      out.push({
        url: url.replace(BASE_URL, ''),
        bytes: res.headers.get('content-length'),
        cacheControl: res.headers.get('cache-control'),
        age: res.headers.get('age'),
        etag: res.headers.get('etag') ? 'present' : null,
        expires: res.headers.get('expires'),
      });
    } catch (error) {
      out.push({ url, error: error.message });
    }
  }
  return out;
}

let chrome;
let browser;
let page;
try {
  chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
  });
  // One browser, one page, reused for every run. That is what makes the second
  // navigation to a route a *warm* run: the HTTP cache is still populated from
  // the first. Launching per run would make every run cold and the distinction
  // the file claims to draw would be fiction.
  browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${chrome.port}` });
  page = await browser.newPage();
} catch (error) {
  unmeasurable([
    'Chrome could not be launched or driven, so nothing was measured.',
    `  ${error.message.split('\n')[0]}`,
    '  Lighthouse needs a Chrome binary. Install one, or set CHROME_PATH.',
  ]);
}

const results = [];
try {
  for (const route of CFG.routes) {
    const url = BASE_URL + route.path;
    // The status the measurement is allowed to trust. A route that starts
    // answering 500 must fail the gate, not be reported as a fast error page.
    const expected = route.expectStatus ?? 200;

    const head = await fetch(url, { redirect: 'follow' });
    const status = head.status;
    if (status !== expected) {
      unmeasurable([
        `${route.path} answered HTTP ${status}; the budget set expects ${expected}.`,
        '  a gate that measures a broken page and calls it fast is worse than no gate.',
        `  (role: ${route.role})`,
      ]);
    }

    const cold = [];
    const warm = [];
    const breakdowns = [];
    const transfers = [];
    let retries = 0;

    for (let i = 0; i < RUNS.cold + RUNS.warm; i += 1) {
      const pass = i < RUNS.cold ? 'cold' : 'warm';
      // One page, reused: navigation 1 has an empty HTTP cache, the rest do not.
      // Since Lighthouse 11 the Node entry point resolves to a RunnerResult
      // ({lhr, artifacts, runnerResult}), not to the report itself.
      const outcome = await lighthouse(url, LIGHTHOUSE_FLAGS, undefined, page);
      const lhr = outcome?.lhr ?? outcome;
      if (!lhr?.audits) {
        unmeasurable([
          `${route.path} (${pass}): Lighthouse returned a report with no audits.`,
          `  top-level keys: ${Object.keys(outcome ?? {}).join(', ') || '(none)'}`,
        ]);
      }
      let row = {
        pass,
        lcpMs: num(lhr, 'largest-contentful-paint'),
        cls: num(lhr, 'cumulative-layout-shift'),
        tbtMs: num(lhr, 'total-blocking-time'),
        ttfbMs: num(lhr, 'server-response-time'),
        fcpMs: num(lhr, 'first-contentful-paint'),
        speedIndexMs: num(lhr, 'speed-index'),
        performanceScore: lhr.categories?.performance?.score ?? null,
      };

      // The first navigation on a page Lighthouse has just been handed comes
      // back with no numeric value for any metric — the page is still coming up
      // and the trace records nothing. That is a broken run, not a fast one, and
      // taking it at face value would be reporting an absence of measurement as
      // a measurement. Re-run the *same* navigation and count the retry. This
      // does not select a favourable value: it only replaces a run that produced
      // no number at all. Retries are printed and stored, so a run that needed
      // many of them is visible rather than laundered.
      let attempt = 0;
      while (attempt < MAX_RUN_RETRIES && row.lcpMs === null) {
        attempt += 1;
        retries += 1;
        process.stderr.write(`  ${route.id.padEnd(9)} ${pass} run ${i + 1} returned no metrics; retry ${attempt}\n`);
        const again = await lighthouse(url, LIGHTHOUSE_FLAGS, undefined, page);
        const lhr2 = again?.lhr ?? again;
        row = {
          pass,
          lcpMs: num(lhr2, 'largest-contentful-paint'),
          cls: num(lhr2, 'cumulative-layout-shift'),
          tbtMs: num(lhr2, 'total-blocking-time'),
          ttfbMs: num(lhr2, 'server-response-time'),
          fcpMs: num(lhr2, 'first-contentful-paint'),
          speedIndexMs: num(lhr2, 'speed-index'),
          performanceScore: lhr2.categories?.performance?.score ?? null,
        };
      }

      if (pass === 'cold') {
        cold.push(row);
        breakdowns.push(lcpBreakdown(lhr));
        transfers.push(transfer(lhr));
      } else {
        warm.push(row);
      }
      process.stderr.write(
        `  ${route.id.padEnd(9)} ${pass} run ${i + 1}/${RUNS.cold + RUNS.warm}` +
          `  LCP ${row.lcpMs === null ? 'n/a' : Math.round(row.lcpMs)}ms` +
          `  CLS ${row.cls === null ? 'n/a' : row.cls.toFixed(3)}` +
          `  TBT ${row.tbtMs === null ? 'n/a' : Math.round(row.tbtMs)}ms` +
          `${attempt ? `  (${attempt} retr${attempt === 1 ? 'y' : 'ies'})` : ''}\n`,
      );
    }

    results.push({
      id: route.id,
      path: route.path,
      role: route.role,
      buildEvidence: route.buildEvidence ?? null,
      status,
      retries,
      cold: cold.map((r) => r),
      warm: warm.map((r) => r),
      lcpBreakdown: breakdowns[0] ?? null,
      transfer: transfers[0] ?? null,
      fontHeaders: await fontHeaders(transfers[0]?.fontUrls ?? []),
    });
  }
} finally {
  // `kill()` is synchronous and returns void, and a throw here would replace
  // whatever error the measurement loop was already raising.
  try {
    await browser?.disconnect();
  } catch {
    /* the browser is going away regardless */
  }
  try {
    chrome?.kill();
  } catch {
    /* Chrome is already gone. The measurement result is what matters. */
  }
}

// ── did we actually measure? ─────────────────────────────────────────────────

for (const r of results) {
  if (r.cold.length < RUNS.cold) {
    unmeasurable([
      `${r.path}: ${r.cold.length} of ${RUNS.cold} cold runs completed.`,
      '  a median over fewer runs than asked for is not the measurement that was requested.',
    ]);
  }
  if (r.warm.length < RUNS.warm) {
    unmeasurable([
      `${r.path}: ${r.warm.length} of ${RUNS.warm} warm runs completed.`,
      '  a p75 over fewer samples is not a p75.',
    ]);
  }
  for (const pass of ['cold', 'warm']) {
    for (const [metric, label] of [
      ['lcpMs', 'LCP'],
      ['cls', 'CLS'],
      ['tbtMs', 'TBT'],
      ['ttfbMs', 'TTFB'],
    ]) {
      if (r[pass].some((row) => row[metric] === null)) {
        unmeasurable([
          `${r.path} (${pass}): the report carried no numeric value for ${label}.`,
          '  the budget covers it, so the gate has nothing to compare and will not pass.',
        ]);
      }
    }
  }
}

// ── write the results, always ────────────────────────────────────────────────

mkdirSync(RESULTS_DIR, { recursive: true });
const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const RUN_PATH = join(RESULTS_DIR, `run-${stamp}.json`);
const run = {
  tool: 'check-cwv.mjs',
  lighthouse: 'from apps/web devDependencies',
  baseUrl: BASE_URL,
  measuredAt: new Date().toISOString(),
  runs: RUNS,
  budgets: CFG.budgets,
  provenance: CFG.provenance ?? null,
  results,
};
writeFileSync(RUN_PATH, `${JSON.stringify(run, null, 2)}\n`);

const summarise = (rows, metric) => quantiles(rows.map((r) => r[metric]));

if (COLLECT_ONLY) {
  console.log(`\ncollected ${results.length} route(s) into ${RUN_PATH}`);
  console.log('collect mode: budgets were not enforced. Run without --collect to gate.');
  process.exit(0);
}

// ── the gate ─────────────────────────────────────────────────────────────────

const B = CFG.budgets;
let failures = 0;
const lines = [];
const say = (s = '') => lines.push(s);

say();
say(`Core Web Vitals — ${BASE_URL}`);
say(`budgets from ${CONFIG_PATH.slice(REPO_ROOT.length + 1)} · ${RUNS.cold} cold + ${RUNS.warm} warm runs per route`);
say();

for (const r of results) {
  say(`${r.path}   (${r.role})`);
  const checks = [
    ['LCP', 'lcpMs', B.lcpMs, 0, 'ms', 'cold'],
    ['LCP', 'lcpMs', B.lcpMs, 0, 'ms', 'warm'],
    ['CLS', 'cls', B.cls, 3, '', 'cold'],
    ['CLS', 'cls', B.cls, 3, '', 'warm'],
    ['TTFB', 'ttfbMs', B.ttfbMs, 0, 'ms', 'cold'],
    ['TTFB', 'ttfbMs', B.ttfbMs, 0, 'ms', 'warm'],
    ['TBT (proxy for INP — not INP)', 'tbtMs', B.tbtProxyBudgetMs, 0, 'ms', 'cold'],
    ['TBT (proxy for INP — not INP)', 'tbtMs', B.tbtProxyBudgetMs, 0, 'ms', 'warm'],
  ];
  for (const [label, metric, budget, dp, unit, pass] of checks) {
    const q = summarise(r[pass], metric);
    const bad = q.p75 > budget;
    if (bad) failures += 1;
    const med = q.median.toFixed(dp);
    const p75 = q.p75.toFixed(dp);
    say(
      `  ${pass.padEnd(4)} ${label.padEnd(32)} median ${med.padStart(9)}${unit}` +
        `   p75 ${p75.padStart(9)}${unit}   budget ${String(budget).padStart(7)}${unit}  ${bad ? 'FAIL' : 'ok'}`,
    );
  }

  // The plan's own budget, §3.2: 200 kB of initial JavaScript.
  if (r.transfer) {
    const js = r.transfer.javascriptBytes;
    const bad = js > B.javascriptTransferBytes;
    if (bad) failures += 1;
    say(
      `  cold JS transfer    ${(js / 1024).toFixed(1).padStart(9)} kB` +
        `            budget ${(B.javascriptTransferBytes / 1024).toFixed(0).padStart(6)} kB  ${bad ? 'FAIL' : 'ok'}` +
        `   (plan §3.2)`,
    );
  }
  say();
}

// ── delta against the committed baseline ─────────────────────────────────────

if (existsSync(BASELINE_PATH)) {
  let base;
  try {
    base = JSON.parse(readFileSync(BASELINE_PATH, 'utf8'));
  } catch (error) {
    base = null;
    console.error(`baseline at ${BASELINE_PATH} is unreadable (${error.message}); no deltas shown.`);
  }
  if (base?.results) {
    say(`delta vs ${BASELINE_PATH.slice(REPO_ROOT.length + 1)} (cold p75)`);
    for (const r of results) {
      const prev = base.results.find((b) => b.id === r.id);
      if (!prev) {
        say(`  ${r.id.padEnd(9)} not in baseline — first measurement`);
        continue;
      }
      const parts = [];
      for (const [label, metric, dp, unit] of [
        ['LCP', 'lcpMs', 0, 'ms'],
        ['CLS', 'cls', 3, ''],
        ['TBT', 'tbtMs', 0, 'ms'],
        ['TTFB', 'ttfbMs', 0, 'ms'],
      ]) {
        const now = summarise(r.cold, metric).p75;
        const then = summarise(prev.cold, metric).p75;
        if (then === null || then === undefined) continue;
        const d = now - then;
        parts.push(`${label} ${d >= 0 ? '+' : ''}${d.toFixed(dp)}${unit}`);
      }
      const jsNow = r.transfer?.javascriptBytes ?? null;
      const jsThen = prev.transfer?.javascriptBytes ?? null;
      if (jsNow !== null && jsThen !== null) {
        const d = (jsNow - jsThen) / 1024;
        parts.push(`JS ${d >= 0 ? '+' : ''}${d.toFixed(1)}kB`);
      }
      say(`  ${r.id.padEnd(9)} ${parts.join('  ')}`);
    }
    say();
  }
}

// ── what was not measured, printed where it cannot be missed ─────────────────

say('not measured, and not claimed:');
say(`  INP — field metric. Budget ${CFG.fieldBudgetsNotAsserted?.inpMs ?? 200} ms is recorded in the config and`);
say('        asserted nowhere. What is gated in its place is TBT, named as a proxy above.');
say('  field CLS/LCP at p75 across real users — every number here is a lab run on localhost.');
say('  real-user network and CPU — the throttling is a simulation; no packet left the machine.');
const totalRetries = results.reduce((a, r) => a + (r.retries ?? 0), 0);
say(
  `  ${totalRetries} run(s) across all routes returned no metrics on the first navigation and were re-run.`,
);
say('        A retry replaces a run that produced no number; it never replaces a run that did.');
say();

console.log(lines.join('\n'));

if (failures > 0) {
  console.error(
    `${failures} budget(s) missed. The measured value and the budget are on the line above each failure.`,
  );
  console.error(`full run: ${RUN_PATH.slice(REPO_ROOT.length + 1)}`);
  process.exit(EXIT_BUDGET);
}

console.log('every budget met, and every budget was actually measured.');
console.log(`full run: ${RUN_PATH.slice(REPO_ROOT.length + 1)}`);
process.exit(0);
