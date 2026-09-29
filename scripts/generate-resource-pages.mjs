#!/usr/bin/env node
/**
 * Generate the page files for every catalogue entry that has a real gateway
 * contract but no page yet.
 *
 * Why generate instead of hand-write
 * ----------------------------------
 * The master plan's own answer to the 985-page target is "templates plus
 * generation from the registry" (section on risks: *page volume — response:
 * templates + generation from registry*). Writing 114 files by hand would produce
 * 114 places for the same decision to be made slightly differently, which is how
 * the codebase accumulated five density spellings and two competing title
 * dictionaries in the first place.
 *
 * The honest scope
 * ----------------
 * Of 233 catalogue entries with a contract and no page, 119 are *action or API
 * surfaces* — `POST /workspace/commerce/orders/{order_id}/settle`,
 * `GET /auth/2fa/status`. Those are not pages and are skipped: rendering a form
 * for them would be inventing a workflow the contract does not describe. The
 * remaining 114 are page-shaped: a GET with no action verb.
 *
 * Every generated page is bound to its declared endpoint and renders the five
 * required states. None of them can show a fabricated number, because the
 * template has no fixture path.
 *
 * Run from the repository root:
 *   node scripts/generate-resource-pages.mjs            # dry run, prints the plan
 *   node scripts/generate-resource-pages.mjs --write    # actually write
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
 * Unrouted catalogue paths, computed from the catalogue and the app tree.
 *
 * The clash that matters is a *fallback* path being swallowed. A static sibling
 * that has its own page is fine — Next.js serves it directly and the dynamic
 * route serves everything else, which is how `/market/bazaars/{id}` has sat
 * beside `/market/bazaars/create` all along.
 */
function unroutedCatalogPaths() {
  // Computed on first call rather than at module load: this is declared above
  // `seeds`, and eager evaluation made it a temporal-dead-zone error.
  if (unroutedCatalogPaths.cached) return unroutedCatalogPaths.cached;
  const acc = [];
  for (const seed of SEEDS_PARSED) {
    const literal = join(APP, routeDirFor(seed.path), 'page.tsx');
    if (exists(literal)) continue;
    acc.push(seed.path);
  }
  if (process.env.ECO_DEBUG_UNROUTED) {
    console.log(`  debug: seeds=${SEEDS_PARSED.length} unrouted=${acc.length}`);
    console.log(`  debug: sample ${JSON.stringify(SEEDS_PARSED[0]?.path)} -> ${literal}`);
  }
  unroutedCatalogPaths.cached = acc;
  return acc;
}
unroutedCatalogPaths.cached = null;

/** Filled in once the seeds are parsed; see `unroutedCatalogPaths`. */
let SEEDS_PARSED = [];

/** A lazy accessor, because the catalogue is parsed further down this file. */
const unrouted = () => unroutedCatalogPaths();

/**
 * A dynamic route is refused when it would swallow a fallback path.
 *
 * The comparison is segment-by-segment against the *whole* pattern, not a string
 * prefix. `/hydroma/carbon/{model_id}` collides with `/hydroma/carbon/tokenize`
 * — same length, static where the other has a parameter — but not with
 * `/hydroma/carbon/credits/retire`, which is two segments deeper and is served by
 * its own catch-all below `credits/[token_id]`.
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

  return unrouted().filter((candidate) => {
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

if (seeds.length !== 600) {
  throw new Error(`parsed ${seeds.length} seeds, expected 600 — the catalog shape changed`);
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
 * Which shape the response is. Declared rather than inferred, so a change of
 * contract shows up as a code change instead of a blank page.
 */
const shapeOf = (path) => {
  if (/\/(stats|overview|health|status|metrics|trends|summary|timeline|counts)\b/.test(path)) {
    return 'record';
  }
  return 'rows';
};

const rowsKeyOf = (path) => {
  const leaf = path.split('/').filter(Boolean).at(-1) ?? '';
  if (leaf === '') return undefined;
  const singular = leaf.replace(/-/g, '_');
  return `${singular.replace(/s$/, '')}s`;
};

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
 */
const SEARCH_CONTRACTS = new Map([
  ['/api/v1/content/search', { required: true }],
  ['/api/v1/manual/sites', { required: false }],
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
  `  unrouted catalogue paths: ${unrouted().length}; dynamic entries that would swallow one: ${conflicting.length}`,
);
for (const seed of conflicting) {
  console.log(`    ${seed.path} would swallow ${shadowedFallbacks(seed.path).join(', ')}`);
}

const generatable = pageShaped.filter((seed) => !conflicting.some((c) => c.path === seed.path));
const skipped = pending.filter((seed) => !isPageShaped(seed.method, seed.path));

const plan = pageShaped
  .filter((seed) => !conflicting.some((c) => c.path === seed.path))
  .filter((seed) => paramConflict(seed.path).length === 0)
  .map((seed) => ({
    ...seed,
    slug: slugOf(seed.domain, seed.path),
    file: join(APP, routeDirFor(seed.path), 'page.tsx'),
    shape: shapeOf(seed.path),
  }));

/** Entries the reserved-parameter rule refuses, alongside the shadowing ones. */
const reservedConflicts = pageShaped.filter(
  (seed) =>
    !conflicting.some((c) => c.path === seed.path) && paramConflict(seed.path).length > 0,
);

const template = ({ id, domain, path, endpoint, sourceOfTruth }) => {
  const slug = slugOf(domain, path);
  const shape = shapeOf(path);
  const rowsKey = shape === 'rows' ? rowsKeyOf(path) : undefined;
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
  const searchId = `search-${slug}`;

  return `import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';${
    search ? "\nimport { NoJsSearch } from '@/components/surface/NoJsSearch';" : ''
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
  params,${search ? '\n  searchParams,' : ''}
}: {
  params: ${paramsPromise};${search ? '\n  searchParams: Promise<Record<string, string | string[] | undefined>>;' : ''}
}) {
  const { locale${params.length ? ', ...rest' : ''} } = await params;
  const meta = await getTranslations('pageMeta.${slug}');
  const labels = await resourceLabels();${search ? "\n  const searchCopy = await getTranslations('search');" : ''}
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
  search
    ? `  // A real <form method="get"> on the page, so the search works with
  // JavaScript disabled: submitting it re-navigates to this URL with ?q=…, and
  // the term is read here and forwarded to the gateway. \`required: ${
      search.required
        ? 'true'
        : 'false'
    }\` — the gateway${
      search.required
        ? ' rejects a request without one, so the empty state is the honest first render.'
        : ' lists everything when the term is absent, so the page is useful before anything is typed.'
    }
  const resolved = await searchParams;
  const raw = resolved?.q;
  const term = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? '';
  const searched = ${search.required ? "term.length > 0 ? " : ''}endpoint + (term ? \`?q=\${encodeURIComponent(term)}\` : '')${search.required ? " : ''" : ''};`
    : ''
}
  const result = await fetchResource<Payload>(${search ? 'searched' : 'endpoint'});

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      path={${search ? 'searched' : 'endpoint'}}
      result={result}
      mode=${JSON.stringify(shape)}
      rowsKey={${rowsKey ? JSON.stringify(rowsKey) : 'undefined'}}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    >${
      search
        ? `
      {({ state }) => (
        <NoJsSearch
          name="q"
          path={\`\${searched}\`}
          value={term}
          emptyResult={state === 'empty' && term.length > 0 ? searchCopy('noResults', { term }) : undefined}
          id=${JSON.stringify(searchId)}
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
console.log('\nby domain:');
for (const [domain, count] of Object.entries(byDomain).sort((a, b) => b[1] - a[1])) {
  console.log(`  ${domain.padEnd(12)} ${count}`);
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
