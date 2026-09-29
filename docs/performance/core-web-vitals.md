# Core Web Vitals — measured 2026-09-29

## What could not be measured, first

**INP was not measured and is not claimed anywhere in this report or in the gate.**
INP is a field metric: it is the interaction latency a real person experiences, and
no lab run produces it. Lighthouse has no INP audit. Every number below that stands
where INP would stand is **Total Blocking Time**, Lighthouse's lab proxy, labelled as
a proxy in the output, in the config key name (`tbtProxyBudgetMs`) and in this
sentence. The INP budget of 200 ms is recorded in
`docs/performance/cwv-budgets.json` under `fieldBudgetsNotAsserted` and is asserted
nowhere. The collection endpoint exists at `app/api/observability/web-vitals`; turning
that stream into an assertion needs production traffic this repository does not have.

**Four other things are also not measured, and none of them are estimated:**

- No field data of any kind. Every number is a lab run against `localhost:3107`.
  There are no real users behind any of it.
- The throttling is a **simulation** (Lighthouse `simulate`, desktop preset: 40 ms
  RTT, 10 Mbps, no CPU slowdown). No packet left the machine. A user on a phone on a
  3G cell in a hot train is not modelled by this and is not claimed to be.
- The build under test is identified: `BUILD_ID -P1UfqCGDl99tEz7nGpBc`, finished
  **2026-09-29 12:29:20 UTC**, five minutes before the measurement started at
  12:34:44 UTC. It is a real, complete, `✓ Compiled successfully in 69s` production
  build. Four other agents were editing `apps/web/src/**` and `apps/web/package.json`
  throughout, so the tree was moving around it; §3.2's route table below is from this
  build and later edits are not in it.
- One page shape is absent: there is no signed-in state. Every route measured is
  anonymous. A dashboard behind a session is a different page with a different
  weight, and this report says nothing about it.

**LCP is noisy on three of the six routes and is reported as a distribution, not a
number.** See [Variance](#variance) — this is the single most important caveat in
the document and it changes how the LCP row should be read.

## The build

```
pnpm -C apps/web exec next build     Next.js 15.5.25
BUILD_ID -P1UfqCGDl99tEz7nGpBc       finished 2026-09-29 12:29:20 UTC
✓ Compiled successfully in 69s
✓ Generating static pages (13/13)
First Load JS shared by all routes                        104 kB
  chunks/5305-5c0e6c2671ea60d8.js                          47.6 kB
  chunks/9b6343d0-f12d7eb90ca41bd1.js                      54.2 kB
  other shared chunks (total)                              2.07 kB
356 routes
```

Server: `next start -p 3107`. Lighthouse 13.5.0 (already in `apps/web` devDependencies;
nothing was added). Chrome 153.0.8010.53 headless. 5 cold + 3 warm navigations per
route, 48 navigations total, one browser and one page reused throughout.

## The route set, and why each one is here

The alternatives were rejected for stated reasons, not by preference.

| id | route | why this one | build evidence |
|---|---|---|---|
| `login` | `/en/auth/login` | heaviest public page | `3.59 kB · First Load JS 170 kB` — the heaviest in the table, tied with `/[locale]/auth/signup` (170 kB). The plan's "heaviest public page 170 kB" is confirmed, not quoted. |
| `content` | `/en/market/products` | the majority shape | `4.79 kB · 160 kB`. `apiGet` → `DataStateCard` is what most of the app does, and it is the page the plan's "degrades gracefully without JS" requirement is actually about. |
| `nojs` | `/en/learn/content/search` | the no-JS form | `4.79 kB · 160 kB`. Renders `components/surface/NoJsSearch.tsx`, a real `<form method="get" action="">`. A form that works without JavaScript is a claim; measuring the page it is on is how you check it. |
| `island` | `/en/market/bazaars/demo/map` | the heavy island | `2.78 kB · 119 kB` — **41 kB *below* an ordinary content page.** §3.3 says the bits are in MapLibre, deck.gl and WebGPU and must be lazy. This is the route where that claim is testable. |
| `offline` | `/en/offline` | a neglected state | `298 B · 120 kB`. The offline route is the one nobody opens until they need it. |
| `notfound` | `/en/no-such-page-cwv-probe` | the 404 state | `[...slug] 724 B · 120 kB`; root `/_not-found` 105 kB. |

**Rejected.** `/en` alone — a budget only the home page passes is decoration, and the
home page is not even the heaviest. `/[locale]/prototype` at `9.05 kB · 113 kB` is
the lightest route in the build and would have been the flattering choice. The twelve
`market/checkout/*` routes at ~148–150 kB are a distinct shape (a partially client-
hydrated flow) and would deserve their own set; they are out of scope here, which is
stated rather than hidden. `/[locale]/system/webgpu-fallback` is `298 B · 116 kB` and
renders no WebGPU island, so it would have measured the fallback, not the feature.

## The four vitals

Budget column: LCP 2500 ms, CLS 0.1, TTFB 800 ms — **imported from the web.dev Core
Web Vitals "good" thresholds, not from the plan.** The plan states one performance
budget and it is a *weight*, not a time (§3.2: 200 kB). It states no time budget at
all. These are labelled imported in `docs/performance/cwv-budgets.json` and the
provenance is printed in the gate output. INP is not in this table because it was not
measured.

**LCP, CLS, TBT-proxy and TTFB, cold (p75 of 5) and warm (p75 of 3):**

| route | LCP budget 2500 ms | LCP measured (median / p75) | CLS budget 0.1 | CLS (median / p75) | TTFB budget 800 ms | TTFB (median / p75) | TBT-proxy budget 200 ms | TBT (median / p75) |
|---|---|---|---|---|---|---|---|---|
| `/en/auth/login` | 2500 | **696 / 1436** | 0.1 | 0.003 / 0.003 | 800 | 28 / 30 | 200 | 3 / 3 |
| `/en/market/products` | 2500 | **1337 / 1372** | 0.1 | 0.000 / 0.001 | 800 | 21 / 26 | 200 | 1 / 5 |
| `/en/learn/content/search` | 2500 | **1355 / 1380** | 0.1 | 0.000 / 0.000 | 800 | 28 / 30 | 200 | 5 / 7 |
| `/en/market/bazaars/demo/map` | 2500 | **640 / 648** | 0.1 | 0.000 / 0.000 | 800 | 26 / 29 | 200 | 18 / 29 |
| `/en/offline` | 2500 | **577 / 583** | 0.1 | 0.000 / 0.000 | 800 | 26 / 28 | 200 | 1 / 2 |
| `/en/no-such-page-cwv-probe` | 2500 | **1258 / 1261** | 0.1 | 0.000 / 0.000 | 800 | 24 / 28 | 200 | 25 / 31 |
| **warm** `/en/auth/login` | 2500 | **1512 / 1515** | 0.1 | 0.003 / 0.003 | 800 | 24 / 34 | 200 | 15 / 17 |
| **warm** `/en/market/products` | 2500 | **1339 / 1386** | 0.1 | 0.000 / 0.001 | 800 | 33 / 36 | 200 | 4 / 8 |
| **warm** `/en/learn/content/search` | 2500 | **1338 / 1357** | 0.1 | 0.002 / 0.002 | 800 | 28 / 31 | 200 | 9 / 11 |
| **warm** `/en/market/bazaars/demo/map` | 2500 | **635 / 704** | 0.1 | 0.000 / 0.000 | 800 | 29 / 30 | 200 | 17 / 23 |
| **warm** `/en/offline` | 2500 | **605 / 615** | 0.1 | 0.000 / 0.000 | 800 | 21 / 25 | 200 | 5 / 5 |
| **warm** `/en/no-such-page-cwv-probe` | 2500 | **1259 / 1278** | 0.1 | 0.000 / 0.000 | 800 | 23 / 32 | 200 | 23 / 49 |

**All four metrics pass on all six routes, cold and warm.** Every number is inside
its budget with room. That is the honest headline, and it is a *different* headline
from what §3.2 implies: the app is not slow, on a simulated desktop connection, on
this hardware.

**The budget that fails is the plan's own.** §3.2's 200 kB of initial JavaScript is
missed on four of six routes. That is the table at the bottom of this section.

## Largest contributor to each metric

One contributor per metric, named from the trace, not inferred.

**LCP — element render delay, on every route, without exception.**
`lcp-breakdown-insight` from the observed trace:

| route | timeToFirstByte | elementRenderDelay | sum | LCP element |
|---|---:|---:|---:|---|
| `/en/auth/login` | 33 ms | **257 ms** | 290 ms | `<p class="mt-3 text-sm text-ink-soft">` — "Sign in to reach your land profiles…" |
| `/en/market/products` | 34 ms | **501 ms** | 535 ms | `<p class="mt-3 max-w-2xl text-ink-soft">` — "Products the marketplace has registered…" |
| `/en/learn/content/search` | 43 ms | **489 ms** | 532 ms | `<p class="mt-3 max-w-2xl text-ink-soft">` — "Search the published learning library…" |
| `/en/market/bazaars/demo/map` | 27 ms | **149 ms** | 176 ms | `<div …>Loading map…` |
| `/en/offline` | 30 ms | **139 ms** | 169 ms | `<p class="text-ink-soft">` — "Cached data is available…" |
| `/en/no-such-page-cwv-probe` | 27 ms | **385 ms** | 412 ms | `<p class="text-sm text-ink-soft">` — "The address you followed does not exist…" |

The largest contentful element is **a paragraph of body text on every single
route**. Not a hero image, not a logo, not a video. There is no image to preload and
nothing to `fetchpriority`. TTFB is 27–43 ms observed; element render delay is
139–501 ms. The page is waiting for React to finish and paint, not for a byte on the
wire. Anyone optimising this app for LCP by preloading a hero image would be
optimising something that is not the largest contentful element.

*(These phase durations come from the unthrottled trace; the headline LCP is
Lighthouse's simulated value. They are the same run but different arithmetic, so
they do not sum to it. Stated rather than quietly reconciled.)*

**CLS — nothing dominates, because nothing shifts.** Worst observed value across 48
navigations is **0.003** on `/en/auth/login`; the other five routes are 0.000–0.002.
There is no element contributing more than 0.003 to any measurement. The budget is
0.1, so CLS passes by a factor of 33 on the worst route. Fonts carry
`font-display` and the layout does not reflow when they arrive — which is the thing
the 97-slice CJK problem would have broken, and does not yet.

**TBT-proxy — nothing dominant, and very small.** Worst single value is 49 ms (warm
`notfound`); typical is 0–30 ms. Main-thread work is dominated by React hydration of
the shared 104 kB chunk set. This is the number that suggests INP would be
comfortable, and it is *not* evidence about INP.

**TTFB — the server is not the problem.** 19–36 ms across every route and every pass.
The middleware bundle is 44.8 kB and the routes are server-rendered on demand. There
is no database, cache or upstream in this measurement: `next start` alone was serving.
A production deployment with a cold cache and a real gateway behind it is not
measured here and will be slower.

## Weight, requests, and the font cache

Cold, first navigation, from the Lighthouse network record.

| route | total transfer | requests | JS | CSS | fonts | document | §3.2 budget (JS ≤ 200 kB) |
|---|---:|---:|---:|---:|---:|---:|---|
| `/en/auth/login` | 1156.8 kB | 45 | **241.4 kB** | 46.4 kB | 55.2 kB | 36.3 kB | **FAIL +41.4 kB** |
| `/en/market/products` | 1122.5 kB | 36 | **229.2 kB** | 46.4 kB | 38.2 kB | 37.6 kB | **FAIL +29.2 kB** |
| `/en/learn/content/search` | 1123.6 kB | 36 | **229.2 kB** | 46.4 kB | 38.2 kB | 38.2 kB | **FAIL +29.2 kB** |
| `/en/market/bazaars/demo/map` | 1392.3 kB | 32 | **477.1 kB** | 46.4 kB | 76.7 kB | 33.7 kB | **FAIL +277.1 kB** |
| `/en/offline` | 1075.6 kB | 26 | 193.3 kB | 46.4 kB | 55.2 kB | 32.9 kB | ok |
| `/en/no-such-page-cwv-probe` | 1052.5 kB | 24 | 191.9 kB | 46.4 kB | 33.6 kB | 32.8 kB | ok |

### §3.3 is wrong about the map, and the build table is why nobody caught it

`/[locale]/market/bazaars/[id]/map` has the **lowest** First Load JS of any content
route — 119 kB against 160 kB for `/[locale]/market/products`. That is what §3.3's
"lazy-loaded island" claim looks like in the build output, and it is true. The
measured JavaScript that actually crosses the wire on that route is **477.1 kB** —
2.4× the plan's entire budget, and 248 kB more than the content page that the build
table says is 41 kB *heavier*.

The chunk is deferred, not deferred out of the way. It is requested, downloaded,
parsed and executed inside the measured navigation. A build-time First Load JS
number cannot see the difference between "not in the first payload" and "not in the
first payload but in the first four seconds", and this repository has been reading
the first one as if it were the second. **§3.3's claim that the bits are lazy is
true for the build table and false for the page.**

That is the finding that mattered, and it is the one the missing gate existed to
surface. The gate now fails on it.

### Fonts — cache headers, and why this section is a moving target

**Cache headers are correct as of this build.** Every `.woff2` measured returns:

```
cache-control: public, max-age=31536000, immutable
etag: present
```

across `/en/auth/login`, `/en/market/products`, `/en/learn/content/search`,
`/en/market/bazaars/demo/map`, `/en/offline` and `/en/no-such-page-cwv-probe`. No
font is revalidated on repeat navigation.

**The `maxEntries: 80` bug is already fixed in the tree I built.** `apps/web/src/app/sw.ts`
now has a dedicated font route matched *before* the general static-asset route:

```ts
const FONT_CACHE_MAX_ENTRIES = 112;          // sw.ts:49
{ matcher: … FONT_FILE.test(url.pathname),
  handler: new CacheFirst({ cacheName: 'fonts-v1', plugins: [
    new ExpirationPlugin({ maxEntries: FONT_CACHE_MAX_ENTRIES, maxAgeSeconds: 365 * 24 * 3600 })] }) }
{ matcher: /\.(?:js|css|png|jpg|jpeg|svg|webp|avif|ico)$/i,          // sw.ts:88
  handler: new StaleWhileRevalidate({ cacheName: 'static-assets-v1',
    plugins: [new ExpirationPlugin({ maxEntries: 80, … })] }) }
```

Fonts no longer share the 80-entry budget, and the font extensions were removed from
the `static-assets-v1` pattern on purpose so one file cannot sit in two caches with
two limits. **This section is a moving target: an agent titled "Fix the CJK
stylesheet regression" is still running, and everything below is a snapshot of the
tree at 12:0x, not a stable number.**

**The 97 CJK slices are real and still expensive.** Measured directly, one browser,
one cold load each, `networkidle0`:

| page | font requests | font bytes | cache-control |
|---|---:|---:|---|
| `/zh/` | **14** | **670.3 kB** | `public, max-age=31536000, immutable` |
| `/zh/learn/manual/sites` | 17 | 44.5 kB | same |
| `/fa/` | 21 | 80.0 kB | same |
| `/hi/` | 22 | 118.4 kB | same |

`/zh/` pulls **14 `noto-sans-sc-*.woff2` slices totalling 670.3 kB** — more than three
times the plan's total JavaScript budget, in fonts, on one page. `/en/*` pulls 2–3
Latin faces totalling 33–55 kB. The `unicode-range` mechanism is doing exactly what
it should (fetching only the slices whose glyphs are on screen) and the CJK font is
simply large when you need 14 of its 97 parts. The §3.2 line "17 kB brotli of CJK
font on every page" does not describe what I measured; what I measured is 670 kB on
`/zh/` and near-zero on `/en/*`, which is a *much* better property if the stylesheet
move lands, and a much worse number in the meantime.

## Variance

`/en/auth/login` cold LCP samples: **690, 696, 1436, 547, 1437 ms.**
`/en/market/products` cold: 1381, 352, 1372, 1337, 1336 ms.

These are **bimodal**, not noisy around a mean. Two clusters roughly 750 ms apart,
and the samples do not fill the gap. A single run on `/en/auth/login` would have
reported 547 ms or 1437 ms depending on which one you happened to take, and the
difference between "comfortably fast" and "slow for no visible reason" is entirely
in which navigation got recorded. This is why the gate reports median and p75 and
refuses to run with fewer samples than the config asks for.

The cause was not isolated. The most likely candidates are a race in when the
font-swap completes and which element is largest at paint time — the LCP element is
text in both modes, so the element changes, not just its paint time — but that is a
hypothesis, and this report does not assert it as a finding.

`/en/no-such-page-cwv-probe` had one cold outlier at 2461 ms (FCP 1152 ms against
339–426 ms on the other four runs). It is inside the 2500 ms budget by 39 ms. **A
single sample is carrying that route's p75 and the margin is not real.** If a future
run puts two outliers in five, that route fails.

**The measurement is sensitive to machine load, and this was measured rather than
assumed.** The 48-navigation baseline ran with three retries out of 48 navigations
(6%). Two later runs on a machine at 100% load — eight logical processors, thirteen
node processes, ten Chrome processes, all belonging to other agents — produced
reports with no metric values in roughly a quarter of their navigations, and the
gate exited `2` on both. Lighthouse on a saturated machine returns a report; it just
often returns one with nothing in it. Anyone wiring this into CI should expect a
slower, more contended machine to produce **exit 2 and not a red metric**, and should
read exit 2 as "this host could not measure", not as "the app is fine" and not as
"the app is broken". That distinction is why the code exists.

## The 404 serves HTTP 200

`/en/no-such-page-cwv-probe` returns **HTTP 200** with `<meta name="robots"
content="index, follow">`, a 115,248-byte HTML document, and no `<h1>`. It is not a
404 by any of the three definitions that matter — status, indexing, or size. The body
is correct (it says the address does not exist); the envelope is wrong. A crawler
that treats a 200 as a document indexes a page whose entire content is "this does
not exist", once per unknown URL, forever.

This is not a performance defect, but it was found by measuring it, and it is
recorded here rather than dropped because it fell outside the budget table. It is not
the gate's job to fix, and the gate will keep passing it at `expectStatus: 200`
until someone changes that field to `404` in
`docs/performance/cwv-budgets.json` — at which point the gate will **fail loudly**,
which is the intended behaviour for a route that starts answering 500.

## The gate

`scripts/check-cwv.mjs` — **replaced, not repaired.** See below.

```
pnpm -C apps/web test:cwv          # the script
CWV_BASE_URL=http://localhost:3001 pnpm -C apps/web test:cwv
node scripts/check-cwv.mjs --runs 3        # fewer samples, faster loop
node scripts/check-cwv.mjs --collect      # measure, write results, gate nothing
CWV_CONFIG=./scratch.json node scripts/check-cwv.mjs   # gate a scratch budget set
```

`CWV_CONFIG` and `CWV_RESULTS_DIR` exist so the gate can be pointed at a throwaway
budget set when testing the gate itself — that is what the negative test below used,
and it is why the negative test cost two navigations instead of forty-eight. The
committed default decides anything; an override decides nothing on its own.

**What it does.** Launches Chrome, drives the Lighthouse Node API, navigates each
route in `docs/performance/cwv-budgets.json` five times cold and three times warm in
one browser and one page, extracts LCP/CLS/TBT/TTFB plus the LCP phase breakdown plus
the per-class transfer breakdown, reads the font response headers off the running
server, writes `docs/performance/results/run-<timestamp>.json`, prints a table
against the budgets, prints a delta against the committed baseline, and exits.

**Pass/fail semantics.**

| exit | meaning |
|---|---|
| `0` | every budget met **and every budget was measured** |
| `1` | measured, and at least one budget was missed |
| `2` | **could not measure** |

`2` is the whole point. These are failures, never passes:

- `lighthouse` not resolvable from `apps/web`
- Chrome will not launch or will not accept a Puppeteer session
- nothing answering at `CWV_BASE_URL/health`
- a route answering a status other than its `expectStatus`
- fewer runs completed than `runs.cold` / `runs.warm` ask for — *a p75 over three
  samples is not a p75*
- the report carrying no numeric value for a metric a budget covers
- a navigation that returned no metrics at all more than `MAX_RUN_RETRIES` times

A run whose first navigation returns no metrics is re-run (max 2) and **counted and
printed**. Three such retries happened in the 48-navigation run. That replaces a run
which produced *no number at all*; it never replaces a run that produced one, and no
value is ever selected for being favourable. This is the exact failure mode this
repository keeps finding in token references, in colour utilities and in contrast: a
check that passes because it ran nothing. It is listed as the rule the file is most
careful about, and `2` exists so a machine can tell "the app regressed" from "I have
no idea what the state is".

**Comparability.** Every run writes a full result file; the gate prints a delta
against `docs/performance/results/baseline.json` (cold p75, plus JS transfer in kB),
so a regression is a number with a sign rather than a red build:

```
delta vs docs/performance/results/baseline.json (cold p75)
  login     LCP +0ms  CLS +0.000  TBT +0ms  TTFB +0ms  JS +0.0kB
  island    LCP +0ms  CLS +0.000  TBT +0ms  TTFB +0ms  JS +0.0kB
```

### Negative test

Run against a **scratch** config with a single route — `/en/market/bazaars/demo/map`,
chosen because it has the largest measured JavaScript so a one-route test still
exercises every budget — and `--runs 1`, so the test costs two navigations instead of
forty-eight. The committed budget set was not touched. Verbatim, with the process
exit code as printed.

**A. Fail.** `budgets.lcpMs` set to `1` — a value no page on earth can meet.
Everything else untouched, including §3.2's real 200 kB:

```
  island    cold run 1/2  LCP 654ms  CLS 0.000  TBT 69ms
  island    warm run 2/2  LCP 371ms  CLS 0.000  TBT 20ms

/en/market/bazaars/demo/map   (scratch: the route with the largest measured JS, so a single-route test still exercises every budget)
  cold LCP                              median       654ms   p75       654ms   budget       1ms  FAIL
  warm LCP                              median       371ms   p75       371ms   budget       1ms  FAIL
  cold CLS                              median     0.000   p75     0.000   budget     0.1  ok
  warm CLS                              median     0.000   p75     0.000   budget     0.1  ok
  cold TTFB                             median        42ms   p75        42ms   budget    800ms  ok
  warm TTFB                             median        36ms   p75        36ms   budget    800ms  ok
  cold TBT (proxy for INP — not INP)    median        69ms   p75        69ms   budget    200ms  ok
  warm TBT (proxy for INP — not INP)    median        20ms   p75        20ms   budget    200ms  ok
  cold JS transfer        477.1 kB            budget    200 kB  FAIL   (plan §3.2)

3 budget(s) missed. The measured value and the budget are on the line above each failure.
EXIT CODE: 1
```

**B. Pass.** LCP restored to 2500 and `javascriptTransferBytes` raised to `512000` —
above every measured value — purely to exercise the exit-0 branch:

```
  island    cold run 1/2  LCP 580ms  CLS 0.000  TBT 62ms
  island    warm run 2/2  LCP 648ms  CLS 0.000  TBT 20ms

/en/market/bazaars/demo/map   (scratch: …)
  cold LCP                              median       580ms   p75       580ms   budget    2500ms  ok
  warm LCP                              median       648ms   p75       648ms   budget    2500ms  ok
  cold CLS                              median     0.000   p75     0.000   budget     0.1  ok
  warm CLS                              median     0.000   p75     0.000   budget     0.1  ok
  cold TTFB                             median        37ms   p75        37ms   budget    800ms  ok
  warm TTFB                             median        38ms   p75        38ms   budget    800ms  ok
  cold TBT (proxy for INP — not INP)    median        62ms   p75        62ms   budget    200ms  ok
  warm TBT (proxy for INP — not INP)    median        20ms   p75        20ms   budget    200ms  ok
  cold JS transfer        477.1 kB            budget   500 kB  ok   (plan §3.2)

every budget met, and every budget was actually measured.
EXIT CODE: 0
```

**C. Could not measure is also a failure, and that was demonstrated accidentally.**
An earlier attempt at test A ran the full six-route set with `lcpMs: 1` on a machine
at 100% load with four other agents building. Lighthouse kept returning reports with
no metric values, the retries ran out, and the gate refused:

```
CWV gate could not measure. This is a failure, not a pass.

  /en/learn/content/search (cold): the report carried no numeric value for LCP.
    the budget covers it, so the gate has nothing to compare and will not pass.
EXIT CODE: 2
```

This is the property the whole file is built around, caught in the act. The gate had
a budget it could not evaluate and it did not pass. Under the plan's real budget set
the same run also exits `1` — the full 48-navigation run in `results/` ends
`4 budget(s) missed` / exit `1`, which is the same four JavaScript failures listed
above.

**The committed budget is the plan's 200 kB, and with it the gate currently exits
`1`.** That is not a broken gate — it is the gate doing the job it was written for
on the first day it ran. Four of six routes ship more JavaScript than §3.2 allows.
The pass-path run above used a raised budget *only* to prove the exit-0 branch works;
it is not the configuration that is committed.

## What `check-cwv.mjs` was, and why it was replaced

It was **both** defects at once, which is why the distinction matters and why I am
answering it precisely rather than picking one.

**First, a correction to the brief I was given:** the file is not untracked. It is in
`HEAD` (`git show HEAD:scripts/check-cwv.mjs` returns the old 58-line version), and
`test:cwv` is committed in `apps/web/package.json`. So it was not a script someone
left in the working tree — it was a script that was **committed, wired into
`package.json`, and had never once succeeded**. That is worse than untracked, and it
is what the evidence below shows.

Specifically:

1. **It could not have failed, even if Lighthouse had run.** The budgets lived in
   `apps/web/lighthouserc.json`, an **LHCI** config. The script invoked the
   **`lighthouse` CLI**, which does not read LHCI configs, and whose exit code is `0`
   whenever it produced a report — regardless of the scores in that report. The script
   then printed `CWV budgets met for ${BASE_URL}`. The file's final line was
   unconditional. It was a check that reported success by construction.
2. **The command was not a Lighthouse invocation.** `npx --no-install lighthouse
   --config-path <lhci.json>` passes an LHCI `ci` block to a flag that expects a
   Lighthouse *user* config (`chromeFlags`, `extends`, `settings`), and gives the CLI
   no URL to audit. The file it named has been tracked and unmodified in the tree and
   is read by nothing.
3. **It required a hand-started server** and was not in the `quality` chain, so
   nothing ever started it. `pnpm quality` runs lint, format, types, tests, i18n,
   site-url and tokens. It never loaded a page.

**Replaced rather than repaired.** There was no part of the old file worth keeping —
its one genuinely good decision was refusing to pass silently, and that idea is the
entire spine of the replacement. Repairing it in place would have left the same
structure, the same external-server dependency, and the same "print success after a
command that cannot fail" shape. `@lhci/cli` is not installed and
`apps/web/lighthouserc.json` is still tracked and still read by nothing; a new
root `.lighthouserc.json` now exists for anyone who wants to install it, and says in
its own header that it is inert until they do.

## Wiring into `quality`

**Not wired. `apps/web/package.json` was being edited concurrently for the whole of
this task** (last modified 15:30:43, `M` in `git status` for the duration), and
`test:cwv` sits at line 25 and `quality` at line 29 of a file another agent owns.
Editing it would have been the collision this brief warned about.

The line to add, to `apps/web/package.json`:

```json
"quality": "pnpm lint && pnpm format:check && pnpm type-check && pnpm test && pnpm i18n:compile && pnpm check:site-url && pnpm check:tokens && pnpm test:cwv"
```

**Read this before adding it: `test:cwv` requires a running production server and
exits `2` when there is none.** It will not start one, on the grounds that a build
left running is a build nobody stops. So appending it to `quality` turns every local
`pnpm quality` red for anyone who has not started `next start` first. Two honest
options, and this is a decision for the repository owner rather than for me:

- **Add it to `quality` as above**, and accept that `pnpm quality` now means "with a
  production server running". Document that in `AGENTS.md` next to the other gates.
- **Leave `quality` alone and make the check a release gate instead**, run in CI
  where the build is already a step:
  ```json
  "test:cwv": "node ../../scripts/check-cwv.mjs",
  "quality:perf": "pnpm build && pnpm start -- -p 3107 & sleep 20 && pnpm test:cwv"
  ```
  — noting that the `&`/`sleep` form is Unix-shaped and is written here as a sketch,
  not as a command I ran.

`test:cwv` already exists in `package.json` and needs no edit. **No dependency was
added**: `lighthouse@^13.5.0` is already in `apps/web` devDependencies and
`apps/web/node_modules/lighthouse` was already present, so the "add a dependency
after checking what is installed" question resolved itself in favour of adding
nothing.

## Reproducing

```bash
pnpm -C apps/web build
pnpm -C apps/web exec next start -p 3107      # in another shell; stop it when done
node scripts/check-cwv.mjs
```

Baseline: `docs/performance/results/baseline.json` — a pinned copy of
`docs/performance/results/run-2026-09-29T12-34-44-009Z.json`, which is the 48-navigation
run these numbers come from, `BUILD_ID -P1UfqCGDl99tEz7nGpBc`, measured
2026-09-29T12:34:44Z, 5 cold + 3 warm per route, 3 retries. The two files are byte-identical;
the run file is kept because that is the path the gate printed, and the baseline is
the path the gate deltas against.
