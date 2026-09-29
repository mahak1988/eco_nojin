#!/usr/bin/env node
/**
 * Generate the page files for every catalogue entry that has a real gateway
 * contract but no page yet, and keep the ones already generated current.
 *
 * Why generate instead of hand-write
 * ----------------------------------
 * The master plan's own answer to the 985-page target is "templates plus
 * generation from the registry" (section on risks: *page volume — response:
 * templates + generation from registry*). Writing 132 files by hand would
 * produce 132 places for the same decision to be made slightly differently,
 * which is how the codebase accumulated five density spellings and two
 * competing title dictionaries in the first place.
 *
 * The honest scope
 * ----------------
 * Of 600 catalogue entries, 256 declare a contract and had no page. 118 of those
 * are *action or API surfaces* — `POST /workspace/commerce/orders/{order_id}/
 * settle`, `GET /auth/2fa/status`. Those are not pages and are skipped: rendering
 * a form for them would be inventing a workflow the contract does not describe.
 * The remaining 132 are page-shaped: a GET with no action verb, whose response
 * shape has been read from the router that serves it (see `CONTRACT_SHAPES`).
 *
 * Every generated page is bound to its declared endpoint and renders the five
 * required states. None of them can show a fabricated number, because the
 * template has no fixture path — and a page whose `rowsKey` names a field the
 * gateway does not send is not generated at all, because that is how an empty
 * state gets rendered on top of a response that arrived.
 *
 * Run from the repository root:
 *   node scripts/generate-resource-pages.mjs              # dry run, prints the plan
 *   node scripts/generate-resource-pages.mjs --write --missing   # absent pages only
 *   node scripts/generate-resource-pages.mjs --write --force    # + refresh generated
 */
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB = join(REPO_ROOT, 'apps', 'web');
const CATALOG = join(WEB, 'src', 'lib', 'domains', 'page-catalog.ts');
const APP = join(WEB, 'src', 'app', '[locale]');
const WRITE = process.argv.includes('--write');
/**
 * Write only the files that do not exist yet.
 *
 * The full-run guard refuses to touch an existing page, which is right but blocks
 * a re-run after a partial generation or after fixing a bug in the template. This
 * mode keeps the guard's safety and lets an incomplete run be finished.
 */
const ONLY_MISSING = process.argv.includes('--missing');

/**
 * A route file path for a catalogue path.
 *
 * The catalogue writes dynamic segments as `{id}` because that is the logical
 * shape of the URL. A Next.js route *directory* has to be `[id]`. Writing `{id}`
 * verbatim created 28 directories literally named `{item_id}`, which Next.js
 * treats as a literal path segment — the route would never match.
 *
 * The catalogue's parameter name is also not always the one already on disk:
 * `apps/web/src/app/[locale]/learn/manual/sites/[siteId]` existed before the
 * catalogue declared `/learn/manual/sites/{site_id}`. Generating `[site_id]`
 * alongside it would give Next.js two different dynamic routes for one level,
 * which it rejects as ambiguous. So an existing directory whose *logical* path
 * already matches is reused, and only genuinely new routes get a new directory.
 */
const routeFilePath = (routePath) => routePath.replace(/\{([^}]+)\}/g, '[$1]');

/** Route files already on disk, as `{ relativeDir, logicalPath }`. */
let existingRoutes = null;
function loadExistingRoutes() {
  if (existingRoutes) return existingRoutes;
  const acc = [];
  const walk = (dir) => {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const item of entries) {
      if (item.name.startsWith('_')) continue;
      const full = join(dir, item.name);
      if (item.isDirectory()) {
        walk(full);
      } else if (item.name === 'page.tsx') {
        const rel = relative(APP, dirname(full)).split(sep).join('/');
        const logical = `/${rel}`
          .replace(/\[\.\.\.(\w+)\]/g, '{$1}')
          .replace(/\[(\w+)\]/g, '{$1}');
        acc.push({ rel, logical });
      }
    }
  };
  walk(APP);
  existingRoutes = acc;
  return acc;
}

/**
 * The route directory for a catalogue path, reusing whatever the app already
 * calls a dynamic segment at each level.
 *
 * Segment-by-segment, because that is the only comparison that is right in all
 * three cases the tree contains:
 *
 *   - the parameter is spelled the same — `/market/bazaars/{id}`;
 *   - it is spelled differently — the catalogue says `{order_id}` where the
 *     directory is `[id]`, and emitting a second directory is the error Next.js
 *     reports as "you cannot use different slug names for the same dynamic path",
 *     which fails every route in the app, not just the new one;
 *   - the leaf differs but the parent is shared — `/market/orders/{order_id}/track`
 *     belongs under the existing `[id]`, next to its sibling `tracking`.
 */
function routeDirFor(routePath) {
  const wanted = routePath.split('/').filter(Boolean);

  // An exact match on the whole logical path wins outright.
  for (const existing of loadExistingRoutes()) {
    if (existing.logical === routePath) return existing.rel;
  }

  // Otherwise rebuild the path one level at a time, and at every level that the
  // catalogue calls a parameter, adopt the name the directory already uses.
  let rel = '';
  for (let depth = 0; depth < wanted.length; depth += 1) {
    const parentAbs = join(APP, rel);
    let entries = [];
    try {
      entries = readdirSync(parentAbs, { withFileTypes: true });
    } catch {
      // No directory yet: nothing to adopt.
    }

    // Only a *named* dynamic directory may be adopted. A catch-all must be the
    // last part of a URL, so adopting `[...slug]` and then adding a child under
    // it is the error Next.js reports as "Catch-all must be the last part of the
    // URL" — and, like the slug-mismatch one, it fails every route in the app.
    const adoptable = entries.find(
      (item) => item.isDirectory() && /^\[[^\][.]+\]$/.test(item.name),
    )?.name;

    if (adoptable) {
      rel = rel ? `${rel}/${adoptable}` : adoptable;
      continue;
    }

    // No dynamic directory here. A catch-all sitting at this level means the
    // route cannot be expressed below it, so the entry stays unrouted.
    const catchAll = entries.some(
      (item) => item.isDirectory() && /^\[\[\.\.\.[^\]]+\]\]$/.test(item.name),
    );
    if (catchAll && wanted[depth].includes('{')) return routeFilePath(routePath).slice(1);

    const own = routeFilePath(`/${wanted[depth]}`).slice(1);
    rel = rel ? `${rel}/${own}` : own;
  }

  return rel;
}

const exists = (path) => {
  try {
    readFileSync(path, 'utf8');
    return true;
  } catch {
    return false;
  }
};

/**
 * Regenerate pages this script previously wrote.
 *
 * Safe because it matches on the marker the template emits, not on the file
 * path: a hand-written page that happens to sit where a catalogue entry points
 * is never touched, and a generated page is always brought up to date. Without
 * this, fixing a template bug would leave every previously generated page broken,
 * which is exactly what happened with the duplicated `params:` key.
 */
const FORCE = process.argv.includes('--force');
const GENERATED_MARKER = 'Generated from the page catalogue';

const isGenerated = (path) => {
  try {
    return readFileSync(path, 'utf8').includes(GENERATED_MARKER);
  } catch {
    return false;
  }
};

/**
 * Paths ending in one of these are actions or sub-resources, not pages. A GET on
 * `/ai/health` is a capability probe the platform surfaces; a POST on
 * `/…/settle` is a mutation. Neither is a document to read.
 */
const ACTION_SEGMENTS = new Set([
  'approve', 'cancel', 'cancel-schedule', 'confirm', 'confirm-payment', 'settle',
  'ship', 'mark-delivered', 'pay', 'restart', 'toggle', 'publish', 'schedule',
  'translate', 'share', 'retire', 'transfer', 'generate', 'generate-draft',
  '2fa', 'stream', 'chat', 'advise', 'upload', 'delete', 'create', 'update',
  'submit', 'send', 'verify', 'revoke', 'rotate', 'reset', 'apply', 'accept',
  'reject', 'close', 'resolve', 'escalate', 'archive', 'restore', 'bulk',
  'rerun', 'run', 'preview', 'export', 'import', 'batch',
]);

/** `/market/cart/{product_id}` — a dynamic leaf belongs to its parent page. */
const isPageShaped = (method, path) => {
  if (method !== 'GET') return false;
  const segments = path.split('/').filter(Boolean);
  const last = segments.at(-1) ?? '';
  if (ACTION_SEGMENTS.has(last)) return false;
  // A parameterised tail is a detail route; it is generated only when the
  // parent is a real page, so the two cannot disagree about what exists.
  return true;
};

/**
 * Catalogue paths that could be swallowed, computed from the catalogue and the
 * app tree.
 *
 * The clash that matters is a *fallback* path being swallowed. A static sibling
 * that has its own page is fine — Next.js serves it directly and the dynamic
 * route serves everything else, which is how `/market/bazaars/{id}` has sat
 * beside `/market/bazaars/create` all along.
 *
 * Only a path that can *become a page* is at risk. A `POST` entry — an action or
 * an API surface — is never routed here, so a dynamic segment cannot take it:
 * whatever the dynamic route renders for that URL is not the action the
 * catalogue declared, and the entry was never going to be a page. Counting those
 * as swallowed reported five conflicts that did not exist and suppressed four
 * real GET pages; see `shadowedFallbacks`.
 */
function shadowableCatalogPaths() {
  // Computed on first call rather than at module load: this is declared above
  // `seeds`, and eager evaluation made it a temporal-dead-zone error.
  if (shadowableCatalogPaths.cached) return shadowableCatalogPaths.cached;
  const acc = [];
  for (const seed of SEEDS_PARSED) {
    if (!seed.endpoint) continue;
    if (!isPageShaped(seed.method, seed.path)) continue;
    const literal = join(APP, routeDirFor(seed.path), 'page.tsx');
    if (exists(literal)) continue;
    acc.push(seed.path);
  }
  if (process.env.ECO_DEBUG_UNROUTED) {
    console.log(
      `  debug: seeds=${SEEDS_PARSED.length} shadowable=${acc.length} unrouted=${unroutedCatalogPaths().length}`,
    );
  }
  shadowableCatalogPaths.cached = acc;
  return acc;
}
shadowableCatalogPaths.cached = null;

function unroutedCatalogPaths() {
  if (unroutedCatalogPaths.cached) return unroutedCatalogPaths.cached;
  const acc = [];
  for (const seed of SEEDS_PARSED) {
    const literal = join(APP, routeDirFor(seed.path), 'page.tsx');
    if (exists(literal)) continue;
    acc.push(seed.path);
  }
  unroutedCatalogPaths.cached = acc;
  return acc;
}
unroutedCatalogPaths.cached = null;

/** Filled in once the seeds are parsed; see `shadowableCatalogPaths`. */
let SEEDS_PARSED = [];

/** A lazy accessor, because the catalogue is parsed further down this file. */
const unrouted = () => unroutedCatalogPaths();
const shadowable = () => shadowableCatalogPaths();

/**
 * A dynamic route is refused when it would swallow a page it can be routed for.
 *
 * The comparison is segment-by-segment against the whole pattern, not a string
 * prefix. `/hydroma/carbon/{model_id}` collides with `/hydroma/carbon/tokenize`
 * — same length, static where the other has a parameter — but not with
 * `/hydroma/carbon/credits/retire`, which is two segments deeper and is served by
 * its own catch-all below `credits/[token_id]`.
 *
 * The candidate set is `shadowableCatalogPaths`, not every unrouted entry. That
 * distinction is the whole rule, and getting it wrong was worth four working
 * pages: all five reported "swallows" named a static sibling that is a `POST`
 * mutation (`/market/villages/engagements`, `/hydroma/carbon/verra/search`,
 * `/admin/content/generate-draft`, `/system/iot/devices/provision-qr`,
 * `/hydroma/carbon/tokenize`). A mutation never gets a page, so a dynamic
 * sibling cannot take a route away from it, and refusing the dynamic GET that
 * *does* have a read contract was suppressing the page the contract asked for.
 *
 * Three earlier versions of this rule were wrong in different directions: one
 * refused any dynamic route with a static sibling and deleted twenty working
 * pages; one looked for shadowed siblings only among paths that have a page, so
 * it could never fire; one used a prefix and over-reported. The pattern match is
 * what Next.js itself does, which is the only comparison that cannot be wrong
 * here.
 */
function shadowedFallbacks(routePath) {
  const pattern = routePath.split('/').filter(Boolean);
  if (!pattern.some((segment) => segment.includes('{'))) return [];

  return shadowable().filter((candidate) => {
    const segments = candidate.split('/').filter(Boolean);
    if (segments.length !== pattern.length) return false;
    return pattern.every((segment, index) => {
      const isParam = segment.includes('{');
      if (isParam) return !segments[index].includes('{');
      return segments[index] === segment;
    });
  });
}

const source = readFileSync(CATALOG, 'utf8');

/**
 * Parse the seed array by locating each `id:` and reading the fields that follow
 * inside that entry's own span.
 *
 * A single regex across the whole file is fragile here: one entry
 * (`marketplace-market-categories-4`) wraps its `sourceOfTruth` onto a second
 * line, so a line-anchored pattern silently drops that entry — 599 of 600, with
 * no error. Splitting on the entry boundary first and reading fields within the
 * chunk cannot miss it.
 */
const ENTRY_START = /^[ \t]*id: '([^']+)',/gm;

const bounds = [...source.matchAll(ENTRY_START)];
const seeds = [];
for (let index = 0; index < bounds.length; index += 1) {
  const start = bounds[index].index;
  const end = index + 1 < bounds.length ? bounds[index + 1].index : source.indexOf('\n];', start);
  const chunk = source.slice(start, end === -1 ? source.length : end);

  const field = (name) => {
    // Tolerates CRLF, any indent, and a value wrapped onto the next line.
    // One entry — `marketplace-market-categories-4` — wraps its `sourceOfTruth`,
    // and a single-line pattern silently drops it: 599 of 600, no error. The
    // incomplete check below is what turned that from silent into loud; this is
    // the part that fixes it.
    const match = new RegExp(
      `^[ \\t]*${name}:[ \\t]*(?:\\r?\\n[ \\t]*)?(null|'[^']*')[ \\t]*,[ \\t]*$`,
      'm',
    ).exec(chunk);
    if (!match) return undefined;
    return match[1] === 'null' ? null : match[1].slice(1, -1);
  };

  seeds.push({
    id: bounds[index][1],
    domain: field('domain'),
    path: field('path'),
    endpoint: field('endpoint'),
    method: field('method'),
    sourceOfTruth: field('sourceOfTruth'),
    routeFile: field('routeFile'),
  });
}

const incomplete = seeds.filter(
  (seed) =>
    !seed.domain || !seed.path || seed.endpoint === undefined || !seed.method || seed.routeFile === undefined,
);
if (incomplete.length > 0) {
  throw new Error(
    `could not read every field for ${incomplete.length} entries, e.g. ${incomplete
      .slice(0, 5)
      .map((s) => s.id)
      .join(', ')}`,
  );
}

// 2026-09-29: 600 -> 621. The catalogue gained twenty-one entries whose pages
// already exist on disk: the five `_SPECS` families, the model registry, the
// verification suite, the validation roll-up and the three commerce order
// surfaces. None of their endpoints is in `CONTRACT_SHAPES`, so the undeclared
// list below now names all twenty-one instead of leaving them invisible, and
// `--write --force` still refuses to generate them. That refusal is the point:
// the generator cannot express a `{count, models}` envelope or a bare
// `list[str]`, and a generated page for them would render its empty state over a
// 200 that arrived.
if (seeds.length !== 621) {
  throw new Error(`parsed ${seeds.length} seeds, expected 621 — the catalog shape changed`);
}

const pending = seeds.filter((seed) => seed.endpoint && !seed.routeFile);
SEEDS_PARSED = seeds;

/**
 * What this generator is responsible for, for a *re-run*.
 *
 * An entry that already carries a `routeFile` is still in scope when the file on
 * disk carries this script's marker, so a template fix propagates to every page
 * it previously wrote. An entry with a `routeFile` and a hand-written page is left
 * alone.
 *
 * Restricting to `pending` — the obvious reading — makes the generator disable
 * itself after its first run, which is how 137 pages kept a broken `params:` line
 * long after the fix was in the template.
 */
const owned = seeds.filter(
  (seed) => {
    if (!seed.endpoint) return false;
    const file = join(APP, routeDirFor(seed.path), 'page.tsx');
    // A hand-written page for this path is not ours to regenerate. The catalogue
    // entry keeps its own metadata key, and overwriting the page would replace
    // reviewed content with a template.
    if (exists(file) && !isGenerated(file)) return false;
    return seed.routeFile === null || isGenerated(file);
  },
);
const pageShaped = owned.filter((seed) => isPageShaped(seed.method, seed.path));


/**
 * Names a route parameter uses.
 *
 * The app renders inside a `[locale]` segment, so `locale` is already bound. A
 * catalogue path that declares its own — `/learn/legal/{locale}/{slug}` — would
 * ask Next.js for `{ locale, locale, slug }`, which is a duplicate key in the
 * params type and an ambiguous value at runtime: `/fa/learn/legal/fa/slug` says
 * the same thing twice.
 *
 * Such an entry is declared non-generatable rather than papered over. Emitting a
 * page for it would mean silently dropping one of the two locales, and which one
 * the i18n layer would keep is exactly the kind of decision that belongs in the
 * catalogue rather than in a template.
 */
const RESERVED_PARAMS = new Set(['locale']);

function paramConflict(routePath) {
  const names = [...routePath.matchAll(/\{([^}]+)\}/g)].map((m) => m[1]);
  return names.filter((name) => RESERVED_PARAMS.has(name));
}

/** `/market/cart/{product_id}` -> `market-cart`. Stable, readable, collision-free. */
const slugOf = (domain, path) =>
  `${domain}-${path.split('/').filter(Boolean).join('-')}`.replace(/[{}]/g, '').toLowerCase();

/**
 * The response shape of every contract this generator writes.
 *
 * Each entry is read from the handler that serves it, and each row names where
 * the reading came from. This replaces two functions that guessed.
 *
 * `shapeOf` used to test the route leaf against a list of words — `stats`,
 * `overview`, `health`, `trends` — and `rowsKeyOf` used to pluralise the leaf:
 * `/ai/history` became `historys`, `/admin/errors/{error_id}` became
 * `{error_id}s`, `/manual/crop-params` became `crop_params`. `ResourcePage`
 * reads `(data as Record<string, unknown>)[rowsKey]` and gets `undefined`, so
 * every one of those pages rendered its *empty* state on top of a response that
 * had arrived, with a 200 next to it. The count in the empty state was a
 * fabricated zero.
 *
 * So the shape is declared, per endpoint, from the contract:
 *
 *   ['/api/v1/ai/history', 'rows', 'conversations']
 *   //  ai_chat.py: `return {"count": len(convs), "conversations": [...]}`
 *   ['/api/v1/manual/crop-params', 'rows', 'rows']
 *   //  manual_data.py: `ManualCropsResponse(ManualRowsResponse)` — the envelope
 *   //  key is literally `rows`, whatever the page is about
 *   ['/api/v1/iot/devices', 'rows']
 *   //  iot_devices.py: `return [Device(...), ...]` — a bare list, so `rowsKey`
 *   //  is undefined and `readRows` takes the payload itself
 *   ['/api/v1/auth/me', 'record']
 *   //  auth.py: `user_to_response(current_user)` — one object
 *
 * `rowsKey` is omitted when the response *is* the array. `record` is for a
 * response that is one document, which a table cannot render.
 *
 * An endpoint that is not listed here is not generated. Inventing a key is how
 * the empty-over-data page was produced in the first place, and a missing
 * declaration should stop the run with a message naming the endpoint rather
 * than ship a page that cannot render its own response.
 */
const CONTRACT_SHAPES = [
  // --- AI -------------------------------------------------------------------
  // Two arrays of different length and meaning; neither is the page's subject,
  // so this is a document, not a table.
  ['/api/v1/ai/analysis/providers', 'record'],
  // ai_chat.py: `{"count": len(convs), "conversations": [...]}`
  ['/api/v1/ai/history', 'rows', 'conversations'],
  // support.py: `{"personas": [...]}`
  ['/api/v1/support/personas', 'rows', 'personas'],
  // marketplace.py: totals, with the revenue breakdown nested under `orders`.
  ['/api/v1/marketplace/stats', 'record'],
  ['/api/v1/marketplace/admin/stats', 'record'],
  // ai.py: `{"status": "operational", "engine_type": …, "providers_configured": true}`
  ['/api/v1/ai/health', 'record'],
  // pilot.py: application aggregates.
  ['/api/v1/pilot/stats', 'record'],

  // --- blockchain -----------------------------------------------------------
  // Every `*_health` and `*_stats` here returns a flat capability report.
  ['/api/v1/blockchain/ecocoin/health', 'record'],
  ['/api/v1/blockchain/ecocoin/stats', 'record'],
  ['/api/v1/blockchain/health', 'record'],
  ['/api/v1/blockchain/phasegate/status', 'record'],
  ['/api/v1/blockchain/ecocoin/wallet/{user_id}', 'record'],
  ['/api/v1/blockchain/impact/certificate/{certificate_id}', 'record'],
  ['/api/v1/blockchain/info', 'record'],
  ['/api/v1/blockchain/treasury/balance', 'record'],
  // `{confidence, impact_score, trust_multiplier, …}` for one activity.
  ['/api/v1/blockchain/oracle/metrics/{activity_id}', 'record'],

  // --- marketplace ----------------------------------------------------------
  ['/api/v1/marketplace/admin/orders', 'rows', 'orders'],
  ['/api/v1/marketplace/marketplaces/{marketplace_id}', 'record'],
  ['/api/v1/marketplace/marketplaces/{marketplace_id}/shops', 'rows', 'shops'],
  ['/api/v1/marketplace/orders/{order_id}/track', 'rows', 'timeline'],
  ['/api/v1/marketplace/payments/{payment_id}/escrow', 'rows', 'entries'],
  ['/api/v1/marketplace/producers', 'rows', 'producers'],
  ['/api/v1/marketplace/products', 'rows', 'products'],
  ['/api/v1/marketplace/products/search', 'rows', 'results'],
  ['/api/v1/marketplace/products/{product_id}', 'record'],
  ['/api/v1/marketplace/products/{product_id}/carbon-credits', 'rows', 'credits'],
  ['/api/v1/marketplace/products/{product_id}/trace', 'rows', 'events'],
  ['/api/v1/marketplace/vendors/{vendor_id}', 'record'],
  ['/api/v1/marketplace/vendors/{vendor_id}/orders', 'rows', 'orders'],
  ['/api/v1/marketplace/vendors/{vendor_id}/products', 'rows', 'products'],
  // village_hub.py declares `response_model=list` on all four.
  ['/api/v1/marketplace/villages/b2b/demands/my', 'rows'],
  ['/api/v1/marketplace/villages/b2b/matches/{village_id}', 'rows'],
  ['/api/v1/marketplace/villages/investments', 'rows'],
  ['/api/v1/marketplace/villages/nomadic-communities', 'rows'],
  ['/api/v1/marketplace/villages/opportunities', 'rows'],
  ['/api/v1/marketplace/villages/opportunities/{opportunity_id}/team', 'rows'],
  // `{"profiles": [...], "count": n}`
  ['/api/v1/marketplace/villages/entrepreneurs', 'rows', 'profiles'],
  // `{"exists": bool}`
  ['/api/v1/marketplace/villages/entrepreneurs/me', 'record'],
  // One engagement, not a list of them.
  ['/api/v1/marketplace/villages/projects/{project_id}/engaged', 'record'],
  // village_hub.py:300 — `response_model=dict`, one village profile.
  ['/api/v1/marketplace/villages/{village_id}', 'record'],

  // --- carbon ---------------------------------------------------------------
  ['/api/v1/carbon/credits/balance', 'record'],
  ['/api/v1/carbon/credits/{token_id}/history', 'rows', 'history'],
  ['/api/v1/carbon/verra/standards', 'rows', 'standards'],
  // carbon.py:214 — the Verra registry returns the project document.
  ['/api/v1/carbon/verra/{registry_id}', 'record'],

  // --- hydroma --------------------------------------------------------------
  // hydroma_*.py: `{"count": len(_SPECS), "models": _SPECS}` for all three.
  ['/api/v1/hydroma/carbon', 'rows', 'models'],
  ['/api/v1/hydroma/climate', 'rows', 'models'],
  ['/api/v1/hydroma/economics', 'rows', 'models'],
  // `return spec` — one tool's metadata.
  ['/api/v1/hydroma/carbon/{model_id}', 'record'],
  ['/api/v1/hydroma/climate/{model_id}', 'record'],
  ['/api/v1/hydroma/economics/{model_id}', 'record'],
  // hydroma_ops.py: `return out` — a row/index/journal-mode report.
  ['/api/v1/hydroma/db-stats', 'record'],
  // elevation.py: `return data`
  ['/api/v1/elevation/grid/{site_id}', 'record'],

  // --- hub / science / analytics -------------------------------------------
  ['/api/v1/hub/shared', 'rows', 'runs'],
  ['/api/v1/science/agrovoc', 'rows', 'results'],
  ['/api/v1/science/citations', 'record'],
  // citations.py: `{"count": len(items), "items": [...]}`
  ['/api/v1/science/citations/index', 'rows', 'items'],
  // datasets.py: `{"count": …, "live": …, "datasets": [...], "note": …}`
  ['/api/v1/science/datasets', 'rows', 'datasets'],
  // science.py: `{"count": len(out), "cards": [...]}`
  ['/api/v1/science/model-cards', 'rows', 'cards'],
  ['/api/v1/analytics/activity-timeline', 'rows', 'activities'],
  ['/api/v1/analytics/carbon-summary', 'record'],
  ['/api/v1/analytics/ndvi-trends', 'record'],
  ['/api/v1/analytics/performance-metrics', 'record'],
  ['/api/v1/analytics/scenario-impact', 'rows', 'scenarios'],
  ['/api/v1/analytics/soil-trends', 'record'],

  // --- dashboard ------------------------------------------------------------
  // Every `/dashboard/public/*` returns the same envelope: a status flag around
  // a `data` object, not a list of rows.
  ['/dashboard/data', 'record'],
  ['/dashboard/public/analytics', 'record'],
  ['/dashboard/public/carbon', 'record'],
  ['/dashboard/public/full', 'record'],
  ['/dashboard/public/mrv', 'record'],
  ['/dashboard/public/projects', 'record'],
  ['/dashboard/public/satellite', 'record'],
  ['/dashboard/public/simulations', 'record'],
  ['/dashboard/public/soil', 'record'],
  ['/dashboard/public/tourism', 'record'],
  ['/dashboard/public/weather', 'record'],
  // `available_endpoints` is the only list in the capability probe.
  ['/dashboard/public/test', 'rows', 'available_endpoints'],
  ['/dashboard/recommendations/{farm_id}', 'rows', 'recommendations'],

  // --- IoT ------------------------------------------------------------------
  ['/api/v1/iot/devices', 'rows', 'devices'],
  ['/api/v1/iot/devices/{device_id}/readings', 'rows', 'readings'],
  // iot_devices.py:112 — one device's detail document.
  ['/api/v1/iot/devices/{device_id}', 'record'],

  // --- auth -----------------------------------------------------------------
  // `/api/v1/auth/*` wraps its payload as `{"status": …, "data": …}`; `data` is
  // an object, so every one of these is a document.
  ['/api/v1/auth/achievements', 'record'],
  ['/api/v1/auth/activity/history', 'record'],
  ['/api/v1/auth/api-keys', 'record'],
  ['/api/v1/auth/assets', 'record'],
  ['/api/v1/auth/billing/subscription', 'record'],
  ['/api/v1/auth/legacy', 'record'],
  ['/api/v1/auth/me', 'record'],
  ['/api/v1/auth/notifications', 'record'],
  ['/api/v1/auth/oauth/connections', 'record'],
  ['/api/v1/auth/preferences', 'record'],
  ['/api/v1/auth/preferences/extended', 'record'],
  ['/api/v1/auth/profile/public', 'record'],
  ['/api/v1/auth/rate-limit', 'record'],

  ['/api/v1/auth/2fa/status', 'record'],
  ['/api/v1/auth/account/status', 'record'],
  // --- content / legal / manual --------------------------------------------
  ['/api/v1/content/search', 'rows', 'results'],
  // legal_texts.py: `{"count": len(results), "legal_texts": [...]}`
  ['/api/v1/legal-texts', 'rows', 'legal_texts'],
  // `response_model=list[str]` and `response_model=list[dict]` respectively.
  ['/api/v1/legal-texts/locales', 'rows'],
  ['/api/v1/legal-texts/slugs', 'rows'],
  ['/api/v1/legal-texts/{locale}/{slug}', 'record'],
  ['/api/v1/legal-texts/{locale}/{slug}/versions', 'rows'],
  // manual_data.py: the dataset envelope key is `rows` for every dataset page
  // except `sites`, which publishes its own `ManualSitesResponse`.
  ['/api/v1/manual/crop-calendar', 'rows', 'rows'],
  ['/api/v1/manual/crop-params', 'rows', 'rows'],
  ['/api/v1/manual/soil-regions', 'rows', 'rows'],
  ['/api/v1/manual/sites', 'rows', 'sites'],
  // manual_data.py: `{exists, path, size_mb, tables}` — a deployment report.
  ['/api/v1/manual/status', 'record'],

  // --- admin ----------------------------------------------------------------
  // Each of these declares `response_model=list[…]` or `list[dict]`, so the
  // payload is the array and there is no envelope key to name.
  ['/api/v1/admin/bots', 'rows'],
  ['/api/v1/admin/errors', 'rows'],
  ['/api/v1/admin/models', 'rows'],
  ['/api/v1/admin/settings', 'rows'],
  ['/api/v1/admin/security/logins', 'rows'],
  ['/api/v1/admin/content/{item_id}/translations', 'rows'],
  ['/api/v1/admin/content/{item_id}/versions', 'rows'],
  ['/api/v1/admin/errors/{error_id}', 'record'],
  ['/api/v1/admin/models/{name}', 'record'],
  // Two lists of different meaning plus six counters: a document.
  ['/api/v1/admin/security/audit', 'record'],
  // `PlatformStats`
  ['/api/v1/admin/overview', 'record'],
  // `response_model=list[ChannelHealth]` — the one admin health route that is a
  // list. The old word-list rule called anything with `health` in the path a
  // record, which would have emptied this page over eight channel rows.
  ['/api/v1/admin/overview/health', 'rows'],
  ['/api/v1/admin/overview/metrics', 'record'],
  // `{total, unacknowledged, by_type, by_status}`
  ['/api/v1/admin/errors/summary', 'record'],

  // --- science / analytics / automation --------------------------------------
  // science.py: `default_zenodo_client().status()`
  ['/api/v1/science/zenodo/status', 'record'],
  ['/api/v1/analytics/overview', 'record'],
  // automation.py: `{"status", "agent", "token_configured"}`
  ['/api/v1/automation/health', 'record'],

  // --- commerce / disputes / finance ---------------------------------------
  ['/api/v1/commerce/orders/{order_id}', 'record'],
  // `response_model=list[str]`
  ['/api/v1/commerce/orders/{order_id}/transitions', 'rows'],
  ['/api/v1/disputes/{dispute_id}', 'record'],
  ['/api/v1/finance/accounts', 'rows'],
  ['/api/v1/finance/idempotency/keys', 'rows'],
  ['/api/v1/finance/ledger/accounts/{account_id}/balance', 'record'],
  ['/api/v1/finance/ledger/entries', 'rows'],
  ['/api/v1/finance/ledger/profit-and-loss', 'record'],
  // `TrialBalanceResponse(as_of=…, rows=report["rows"], totals=…)`
  ['/api/v1/finance/ledger/trial-balance', 'rows', 'rows'],
  ['/api/v1/finance/wallet', 'record'],

  // --- farms ----------------------------------------------------------------
  // farms.py: `response_model=list[FarmOut]`
  ['/api/v1/farms', 'rows'],
];

/**
 * The table above is a list of tuples, which is readable; a `Map` of those tuples
 * is not, because `new Map([[k, a, b]])` silently discards `b` and stores `a` as
 * the value. That is not a detail: it read every contract as `{mode: 'rows',
 * rowsKey: undefined}`, which is precisely the guess this table exists to
 * remove — the mode happened to survive and the key did not, so every page came
 * out as a table over an unnamed field. So the tuples are folded into
 * `{ mode, rowsKey }` explicitly, once, from the plain list.
 */
const DECLARED_SHAPES = new Map(
  CONTRACT_SHAPES.map(([endpoint, mode, rowsKey]) => [
    endpoint,
    { mode, rowsKey: rowsKey ?? undefined },
  ]),
);

/** The declared shape, or `null` when the contract has not been read yet. */
const contractShapeOf = (endpoint) => DECLARED_SHAPES.get(endpoint) ?? null;

const shapeOf = (endpoint) => contractShapeOf(endpoint)?.mode ?? 'rows';

const rowsKeyOf = (endpoint) => contractShapeOf(endpoint)?.rowsKey;

/**
 * Contracts that accept a `q` term, and whether a bare GET is still valid.
 *
 * Declared from the gateway signatures rather than guessed from the route name,
 * because the two answers differ and the difference decides whether a form may
 * be rendered at all:
 *
 *   - `required: false` — `q` is optional, so the page is a useful list before
 *     anything is typed and the form is an addition.
 *   - `required: true`  — the endpoint is a 400 without `q` (`content_public.py`
 *     declares `q: str = Query(..., min_length=1)`), so the page shows an error
 *     state on arrival and the form is the only way to reach real content.
 *
 * Both facts come from the routers; neither is invented here.
 *
 * Two more are here for the same reason, found by reading `openapi.json` for a
 * `required` query parameter on every planned contract. Both were rendering a
 * permanent error: `marketplace.py` declares `q: str = Query(...)` on
 * `/products/search`, and `science.py` declares `def model_citation(slug: str)`.
 * A bare GET to either is a 422, so the page could never show anything but an
 * error state. The form is not a nicety on these two, it is the only route to
 * the contract.
 *
 * Two others are *not* here, deliberately. `carbon.py` declares `address: str`
 * on `/credits/balance` and `auth.py` declares `user_id: str` on
 * `/profile/public`; both also 422 without the value, but neither is a search,
 * and giving `/auth/profile/public` a public form that asks a reader to name
 * another user is a decision that belongs to the surface's owner rather than to
 * a generator. Those two pages are reported instead of silently reshaped.
 */
const SEARCH_CONTRACTS = new Map([
  ['/api/v1/content/search', { required: true }],
  ['/api/v1/manual/sites', { required: false }],
  ['/api/v1/marketplace/products/search', { required: true }],
  ['/api/v1/science/citations', { required: true }],
]);

/**
 * Contracts that cannot answer a bare GET and take an *identifier* rather than a
 * term — `carbon.py` declares `address: str` on `/credits/balance`, `auth.py`
 * declares `user_id: str` on `/profile/public`. Both return 422 without the value,
 * so both pages rendered a permanent error state.
 *
 * These were previously only reported. They are now generated with a value form,
 * for three reasons:
 *
 *   1. the transport is identical to a search — a GET, a reader-supplied value,
 *      a server re-render — so `NoJsSearch` with `kind="value"` is the whole fix
 *      and no new component is warranted;
 *   2. the alternative was a page that can never render the contract it was
 *      generated for, which is worse than a form: a reader cannot tell the
 *      difference between "no such address" and "this page is broken";
 *   3. the field is labelled from the parameter name and the contract path, both
 *      language-neutral, so the form needs no fourteenth translation pass.
 *
 * The privacy question on `/auth/profile/public` — whether a *public* surface
 * should let a reader name another user — is real and is recorded here as
 * belonging to the surface's owner. It is not a reason to ship a dead page. If
 * that decision goes the other way, delete the entry from this map and the page
 * reverts to being reported rather than generated with a form.
 */
const VALUE_CONTRACTS = new Map([
  ['/api/v1/carbon/credits/balance', { param: 'address' }],
  ['/api/v1/auth/profile/public', { param: 'user_id' }],
]);

/** The dynamic parameter names a catalogue path declares, in order. */
const paramsOf = (routePath) => [...routePath.matchAll(/\{([^}]+)\}/g)].map((m) => m[1]);

/**
 * Every static route the repository already serves, read from the app tree. A
 * generated dynamic route is refused when it would shadow one of these.
 */
function listStaticRoutes(dir = APP, acc = []) {
  for (const name of readdirSync(dir, { withFileTypes: true })) {
    if (name.name.startsWith('_')) continue;
    const full = join(dir, name.name);
    if (name.isDirectory()) {
      listStaticRoutes(full, acc);
    } else if (name.name === 'page.tsx') {
      const rel = relative(APP, dirname(full)).split(sep).join('/');
      const logical = `/${rel}`.replace(/\[([^\]]+)\]/g, '{$1}').replace(/\{\*[^}]+\}/g, '{*}');
      acc.push(logical === '/' ? '/' : logical);
    }
  }
  return acc;
}

const staticSiblings = listStaticRoutes();

/**
 * Entries the conflict rule refuses — computed from what the catalogue currently
 * claims, not only from what is still pending. A re-run has an empty pending set
 * by design, so a page generated before the rule existed would otherwise never be
 * re-examined.
 */
/**
 * Entries the conflict rule refuses.
 *
 * Scoped to `owned` rather than to seeds carrying a declared `routeFile`:
 * those generated pages have `routeFile: null` in `SEEDS` — the catalogue now
 * derives the field from disk — so filtering on it found nothing and the three
 * shadowing routes were never removed.
 */
const conflicting = owned.filter(
  (seed) => seed.path.includes('{') && shadowedFallbacks(seed.path).length > 0,
);

console.log(
  `  unrouted catalogue paths: ${unrouted().length}; of those routable as pages: ${shadowable().length}; dynamic entries that would swallow one: ${conflicting.length}`,
);
for (const seed of conflicting) {
  console.log(`    ${seed.path} would swallow ${shadowedFallbacks(seed.path).join(', ')}`);
}

const generatable = pageShaped.filter((seed) => !conflicting.some((c) => c.path === seed.path));
const skipped = pending.filter((seed) => !isPageShaped(seed.method, seed.path));

/**
 * Entries whose response shape has not been read from the router.
 *
 * A page in this set is refused rather than generated with a guessed key. The
 * guess is what produced `historys` and `{error_id}s`, and `ResourcePage` turns a
 * wrong key into an empty state over a 200 — a fabricated zero. Not generating is
 * visible; generating a page that cannot render its own response is not.
 */
const undeclared = pageShaped.filter(
  (seed) =>
    !conflicting.some((c) => c.path === seed.path) &&
    paramConflict(seed.path).length === 0 &&
    contractShapeOf(seed.endpoint) === null,
);
if (undeclared.length > 0) {
  console.log(
    `\n  ${undeclared.length} contract(s) have no declared response shape, and will not be generated:`,
  );
  for (const seed of undeclared.slice(0, 20)) {
    console.log(`    ${seed.path}  ->  ${seed.endpoint}  (${seed.sourceOfTruth})`);
  }
}

const plan = pageShaped
  .filter((seed) => !conflicting.some((c) => c.path === seed.path))
  .filter((seed) => paramConflict(seed.path).length === 0)
  .filter((seed) => contractShapeOf(seed.endpoint) !== null)
  .map((seed) => ({
    ...seed,
    slug: slugOf(seed.domain, seed.path),
    file: join(APP, routeDirFor(seed.path), 'page.tsx'),
    shape: shapeOf(seed.endpoint),
  }));

/** Entries the reserved-parameter rule refuses, alongside the shadowing ones. */
const reservedConflicts = pageShaped.filter(
  (seed) =>
    !conflicting.some((c) => c.path === seed.path) && paramConflict(seed.path).length > 0,
);

const template = ({ id, domain, path, endpoint, sourceOfTruth }) => {
  const slug = slugOf(domain, path);
  const shape = shapeOf(endpoint);
  const rowsKey = shape === 'rows' ? rowsKeyOf(endpoint) : undefined;
  const routePath = path;
  const params = paramsOf(routePath);

  // The endpoint carries the same `{id}` placeholders, so it is interpolated from
  // the resolved route params rather than requested as a literal template.
  const endpointExpr =
    params.length === 0
      ? JSON.stringify(endpoint)
      : `String(PATH).replace(/\\{(\\w+)\\}/g, (_m, key) => String(routeParams[key] ?? ""))`;

  const paramsType = params.length
    ? `{\n${params.map((p) => `    ${p}: string;`).join('\n')}\n  }`
    : 'Record<string, never>';

  // Just the *type* of the awaited params object. The destructuring sites add
  // their own `params:` name; emitting the name here too produced
  // `{ params: params: Promise<...> }` and a parse error on every dynamic page.
  const paramsPromise = `Promise<{ locale: string${params.length ? `; ${params.map((p) => `${p}: string`).join('; ')}` : ''} }>`;

  // The canonical URL cannot contain a raw `{id}`, so a dynamic route shows the
  // parameter as a placeholder dot.
  //
  // This has now been wrong twice. The first version emitted the *name*
  // `canonicalPath` into every page, producing `…/faROUTE` on all 128. The fix
  // dropped the name but reintroduced the same defect one level up: this
  // expression is spliced into a generator template literal, so a bare `ROUTE`
  // is interpolated *at generation time* and the literal text `ROUTE` lands in
  // the page, where the server component then concatenates it onto the locale
  // and every Open Graph URL becomes `https://app.eco-nojin.org/faROUTE`. The
  // value must therefore carry its own `${…}` so the *generated* page is what
  // interpolates. `check-page-meta.mjs` now fails on a bare `ROUTE` so the
  // third recurrence has to be deliberate.
  const canonicalExpression = params.length
    ? "${ROUTE.replace(/\\{[a-z_]+\\}/g, '·')}"
    : '${ROUTE}';

  // Does the gateway accept a term on this contract, and is it mandatory?
  const search = SEARCH_CONTRACTS.get(endpoint);
  const value = VALUE_CONTRACTS.get(endpoint);
  /**
   * One descriptor for both kinds, so the template below has a single code path.
   * `required` means the gateway rejects a request without the value, which is
   * what decides whether the empty state is the honest first render or a defect.
   */
  const query = search
    ? { param: 'q', kind: 'search', required: search.required }
    : value
      ? { param: value.param, kind: 'value', required: true }
      : null;
  const queryId = `query-${slug}`;

  return `import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';${
    query ? "\nimport { NoJsSearch } from '@/components/surface/NoJsSearch';" : ''
  }

const SLUG = ${JSON.stringify(slug)};
const ROUTE = ${JSON.stringify(routePath)};
/** The declared contract. A dynamic segment is resolved from the route params. */
const PATH = ${JSON.stringify(endpoint)};

/**
 * Generated from the page catalogue — do not hand-edit.
 *
 * Entry \`${id}\`, domain \`${domain}\`. Source of truth: \`${sourceOfTruth}\`.
 * The endpoint is the declared contract; the page renders one of the five
 * required states and never a fabricated value.
 */
type Payload = Record<string, unknown>;

export async function generateMetadata({ params }: { params: ${paramsPromise} }): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.${slug}');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: \`\${BASE_URL}/\${locale}${canonicalExpression}\`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({
  params,${query ? '\n  searchParams,' : ''}
}: {
  params: ${paramsPromise};${query ? '\n  searchParams: Promise<Record<string, string | string[] | undefined>>;' : ''}
}) {
  const { locale${params.length ? ', ...rest' : ''} } = await params;
  const meta = await getTranslations('pageMeta.${slug}');
  const labels = await resourceLabels();${query && query.kind === 'search' ? "\n  const searchCopy = await getTranslations('search');" : ''}
${
  params.length
    ? `  // A dynamic segment is resolved from the route params rather than requested
  // as a literal template. "rest" is used instead of a second "params" binding,
  // which collided with the destructured parameter and failed to compile.
  const routeParams = rest as Record<string, string>;
  const endpoint = ${endpointExpr};`
    : `  const endpoint = PATH;
`
}${
  query
    ? `  // A real <form method="get"> on the page, so this works with JavaScript
  // disabled: submitting it re-navigates to this URL with the value, and the value
  // is read here and forwarded to the gateway. Kind: ${query.kind} (${JSON.stringify(query.param)}).
  // \`required: ${query.required}\` — the gateway${
      query.required
        ? ' rejects a request without it, so without a form this page could only ever render an error.'
        : ' lists everything when it is absent, so the page is useful before anything is typed.'
    }
  const resolved = await searchParams;
  const raw = resolved?.${/^[A-Za-z_$][\w$]*$/.test(query.param) ? query.param : `[${JSON.stringify(query.param)}]`};
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const searched = ${
    query.required
      ? "term.length > 0 ? `${endpoint}?" +
        query.param +
        '=${encodeURIComponent(term)}` : ""'
      : 'endpoint + (term ? `' +
        '?' +
        query.param +
        '=${encodeURIComponent(term)}`' +
        " : '')"
  };`
    : ''
}
  const result = await fetchResource<Payload>(${query ? 'searched' : 'endpoint'});

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      path={${query ? 'searched' : 'endpoint'}}
      result={result}
      mode=${JSON.stringify(shape)}
      rowsKey={${rowsKey ? JSON.stringify(rowsKey) : 'undefined'}}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    >${
      query
        ? `
      {({ state }) => (
        <NoJsSearch
          kind=${JSON.stringify(query.kind)}
          name=${JSON.stringify(query.param)}
          path={\`\${searched}\`}
          value={term}${
            query.kind === 'search'
              ? "\n          emptyResult={state === 'empty' && term.length > 0 ? searchCopy('noResults', { term }) : undefined}"
              : "\n          // The value kind has no \"no results\" message on purpose: an address\n          // that matches nothing is not a failed search, and a reader who mistyped\n          // a wallet address should be told the field was not found rather than\n          // that a catalogue came up empty. The error state below carries that."
          }
          id=${JSON.stringify(queryId)}
        />
      )}`
        : ''
    }
    </ResourcePage>
  );
}
`;
};

const byDomain = {};
for (const item of plan) byDomain[item.domain] = (byDomain[item.domain] ?? 0) + 1;

console.log(`catalogue entries            : ${seeds.length}`);
console.log(`with a contract, no page     : ${pending.length}`);
console.log(`  page-shaped (will generate): ${plan.length}`);
console.log(`  action/API (skipped)       : ${skipped.length}`);

const gated = plan.filter((item) => VALUE_CONTRACTS.has(item.endpoint));
if (gated.length > 0) {
  console.log('\n  these pages need a reader-supplied value, and are generated with a form:');
  for (const item of gated) {
    console.log(
      `    ${item.path}  ->  ${item.endpoint}  requires ?${VALUE_CONTRACTS.get(item.endpoint).param}`,
    );
  }
  console.log('  Without the form they could only render a permanent error state. To suppress');
  console.log('  the form and go back to reporting them, delete the entry from VALUE_CONTRACTS.');
}
console.log('\nby domain:');
for (const [domain, count] of Object.entries(byDomain).sort((a, b) => b[1] - a[1])) {
  console.log(`  ${domain.padEnd(12)} ${count}`);
}

/**
 * Dump the plan as JSON for inspection: the path, the declared contract, the
 * response shape and the rows key every generated page will read.
 *
 * Set `ECO_DEBUG_PLAN=1`. The ratchets in the test suite are counts, and a count
 * cannot be audited; this is the list a reviewer reads to confirm the contract
 * behind each key.
 */
if (process.env.ECO_DEBUG_PLAN) {
  const dump = join(REPO_ROOT, '.tmp', 'resource-page-plan.json');
  mkdirSync(dirname(dump), { recursive: true });
  writeFileSync(
    dump,
    `${JSON.stringify(
      plan.map((item) => ({
        id: item.id,
        path: item.path,
        endpoint: item.endpoint,
        method: item.method,
        shape: item.shape,
        rowsKey: item.shape === 'rows' ? rowsKeyOf(item.endpoint) : null,
        file: relative(APP, item.file).split(sep).join('/'),
        sourceOfTruth: item.sourceOfTruth,
      })),
      null,
      2,
    )}\n`,
    'utf8',
  );
  console.log(`  debug: plan written to ${dump}`);
}

if (!WRITE) {
  console.log('\ndry run. re-run with --write to generate.');
  process.exit(0);
}

const conflicts = plan.filter((item) => exists(item.file) && !isGenerated(item.file));

if (conflicts.length > 0 && !ONLY_MISSING) {
  console.error(`\nrefusing to overwrite ${conflicts.length} hand-written page(s):`);
  for (const conflict of conflicts.slice(0, 10)) console.error(`  - ${conflict.path}`);
  console.error('\nRe-run with --missing to write only absent pages.');
  process.exit(1);
}

/**
 * What to write.
 *
 * `--force` regenerates only pages this script wrote before, identified by the
 * marker in the file. An earlier version wrote the whole plan under `--force`,
 * which silently replaced eight hand-written `public/education/*` pages — the
 * flag's whole purpose was to make regeneration safe, and it was the opposite.
 */
const toWrite = ONLY_MISSING
  ? plan.filter((item) => !exists(item.file))
  : FORCE
    ? plan.filter((item) => isGenerated(item.file) || !exists(item.file))
    : plan;

let written = 0;
for (const item of toWrite) {
  mkdirSync(dirname(item.file), { recursive: true });
  writeFileSync(item.file, template(item), 'utf8');
  written += 1;
}

console.log(`\nwrote ${written} pages${ONLY_MISSING ? ` (${conflicts.length} already present)` : ''}`);

/**
 * Remove any page a rule now refuses.
 *
 * Note what is *not* here any more: this script used to rewrite 600 `routeFile`
 * lines in the catalogue after writing the pages, and it truncated the file twice
 * doing so. The catalogue now derives `routeFile` from the filesystem inside
 * `buildEntry`, so the generator has nothing to reconcile — a page that exists is
 * a page the catalogue reports, and a page that does not is one it does not. The
 * mutation was the only thing in this file that could damage a source file, and
 * removing it removed the failure mode rather than fixing it.
 */
if (WRITE) {
  for (const seed of [...conflicting, ...reservedConflicts]) {
    const dir = join(APP, routeDirFor(seed.path));
    const file = join(dir, 'page.tsx');
    if (!exists(file) || !isGenerated(file)) continue;
    rmSync(file, { force: true });
    try {
      rmSync(dir, { recursive: true });
    } catch {
      // A non-empty directory holds other routes; leave it.
    }
    const reason = reservedConflicts.includes(seed)
      ? 'a route parameter named "locale" collides with the i18n segment'
      : `it would swallow ${shadowedFallbacks(seed.path).join(', ')}, which only the catalogue catch-all serves`;
    console.log(`removed a generated page: ${seed.path} (${reason})`);
  }
}

// --- pageMeta report --------------------------------------------------------

/**
 * Report which generated slugs still need a `pageMeta` entry.
 *
 * A generated page reads its heading through `getTranslations('pageMeta.<slug>')`,
 * so a missing entry renders next-intl's `MISSING_MESSAGE` — a loud failure, but
 * a failure. This lists the gaps so they can be filled deliberately rather than
 * discovered one page at a time.
 */
const en = JSON.parse(readFileSync(join(WEB, 'messages', 'en.json'), 'utf8'));
const needs = plan
  .map((item) => item.slug)
  .filter((slug) => !en.pageMeta?.[slug]);

const report = join(REPO_ROOT, '.tmp', 'resource-page-meta.json');
mkdirSync(dirname(report), { recursive: true });
writeFileSync(
  report,
  `${JSON.stringify(
    needs.map((slug) => {
      const item = plan.find((entry) => entry.slug === slug);
      return { slug, path: item.path, shape: item.shape };
    }),
    null,
    2,
  )}\n`,
  'utf8',
);

console.log(`\npageMeta still needed: ${needs.length} of ${plan.length}`);
console.log(`  report: ${report}`);
console.log(`\nNext, and not automatic: the pageMeta entries. Add a title and description`);
console.log(`for each of these ${written} slugs to messages/en.json and messages/fa.json,`);
console.log(`or check-page-meta.mjs will fail on the missing key.`);
console.log(`\nSlugs needing pageMeta entries:`);
for (const item of plan) console.log(`  ${item.slug}`);
console.log(`\nCatalogue routeFile values to update: ${plan.length} (planned -> live)`);
console.log(resolve(join(WEB, 'src', 'lib', 'domains', 'page-catalog.ts')));
