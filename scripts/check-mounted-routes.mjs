#!/usr/bin/env node
/**
 * Mounted-route gate.
 *
 * A router that is declared, tested and never `include_router`ed is not a
 * feature -- it is a permanent error state on every page built on it. This
 * gate closes that hole:
 *
 *   1. parse `services/api_gateway/main.py` for every import alias and every
 *      `app.include_router(...)` call, resolving each alias to a real file
 *      (including `from .routers import x`, `from services.x.y import z as w`
 *      and the six-line forwarding shims);
 *   2. walk every `.py` under `services/`, collect every `APIRouter` and every
 *      `@router.get/post/put/patch/delete/head/options` decorator, and compute
 *      the full public path (router prefix + mount prefix + route path);
 *   3. report, per HTTP method, the mounted set and the declared-but-unmounted
 *      set, plus every path collision (two mounted routers serving the same
 *      `METHOD path` -- the first registration wins, the second is dead);
 *   4. exit non-zero when any router under `services/` that is not on the
 *      explicit EXCLUSIONS list declares routes and is not mounted.
 *
 * The exclusion list is printed on every run so it cannot rot silently.
 *
 * Expected exit state today: **1**, on the pre-existing `POST /api/v1/ai/chat`
 * collision only. `services/api_gateway/routers/ai.py:68` is mounted before
 * `services/api_gateway/routers/ai_chat.py:222`, both declare that path, and
 * Starlette resolves first-match-wins -- so the `require_user` handler is dead
 * and the unauthenticated one serves the route. That is an auth decision, not a
 * wiring one, and it is left unresolved on purpose. The unmounted-router count
 * is 0: every declared router is either mounted or carries a stated reason.
 *
 * Usage:  node scripts/check-mounted-routes.mjs [--json] [--quiet] [--plan]
 *         [--verify-runtime <app.openapi() dump.json>]
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative, dirname, sep } from 'node:path';

const ROOT = process.cwd();
const MAIN = join(ROOT, 'services', 'api_gateway', 'main.py');
const SERVICES = join(ROOT, 'services');

const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'];

/**
 * Deliberately unmounted routers.
 *
 * Every entry is a decision with a reason, not a gap. If a router belongs here
 * it must be justified in one line; if it does not, it must be mounted.
 * Anything removed from this list without being mounted fails the gate.
 *
 * The dominant reason is `no auth`: the router carries no `require_user` /
 * `require_admin` / token dependency, so mounting it publishes a surface its
 * mounted neighbours protect. That is a security decision, not a wiring one,
 * and it is the owner's to make -- not this gate's.
 */
const EXCLUSIONS = [
  {
    file: 'services/backup/router.py',
    reason:
      'no auth: unauthenticated POST /api/v1/backup/restore and backup-config enable/disable. Mounted neighbours that touch privileged state (admin_*) all use require_admin_with_mfa.',
  },
  {
    file: 'services/jobs/router.py',
    reason:
      'no auth: unauthenticated create/cancel/retry of compute jobs and read of /jobs/{id}/events. Operator-class surface with no gate.',
  },
  {
    file: 'services/contracts/router.py',
    reason:
      'no auth: unauthenticated POST of service contracts and /{name}/{version}/deprecate mutates the contract registry that services/contracts/tests asserts against.',
  },
  {
    file: 'services/provenance/router.py',
    reason:
      'no auth: unauthenticated writes to the provenance/lineage ledger and /models/{name}/{version}/deprecate. An audit record that anyone can append to is not an audit record.',
  },
  {
    file: 'services/alerting/router.py',
    reason:
      'no auth: /api/v1/alerts/{id}/suppress lets an anonymous caller silence operational alerts; GET /api/v1/alerts/rules exposes configured thresholds.',
  },
  {
    file: 'services/admin/api/__init__.py',
    reason:
      'no auth: prefix /admin with GET /admin/audit-logs and /admin/stats. Every mounted admin_* router requires an admin principal; this one requires none.',
  },
  {
    file: 'services/admin/nojin_admin.py',
    reason:
      'no auth: prefix /admin/nojin with POST /admin/nojin/credits/issue (unauthenticated carbon-credit issuance) and /projects/{id}/verify.',
  },
  {
    file: 'services/ledger/main.py',
    reason:
      'no auth: unauthenticated POST /api/v1/ledger/entries. The file states the decision itself -- "This app is not mounted in the API gateway ... exposes an unauthenticated write endpoint on its own port".',
  },
  {
    file: 'services/ledger/service.py',
    reason:
      'no auth: same /api/v1/ledger prefix with a different route shape (/balance/{account_id} vs /accounts/{account_id}/balance) and the same unauthenticated financial write. services/ledger/main.py delegates its logic here, which makes service.py the canonical one of the pair -- but neither is mountable without a ledger auth dependency.',
  },
  {
    file: 'services/notification/main.py',
    reason:
      'no auth: GET /api/v1/notifications/ has no caller identity and no default filter, so it returns every notification row in the system; POST / takes an arbitrary user_id and dispatches on email/SMS/Telegram.',
  },
  {
    file: 'services/reporting/main.py',
    reason: 'no auth: POST /api/v1/reports/generate and GET /api/v1/reports/{report_id}/download are reachable by report id without a principal.',
  },
  {
    file: 'services/reporting/api/__init__.py',
    reason: 'no auth: unversioned /reports/ duplicate of services/reporting/main.py, with the same unauthenticated generate + fetch-by-id.',
  },
  {
    file: 'services/analytics/api/__init__.py',
    reason:
      'no auth: /analytics/dashboard|sales-summary|tourism-metrics expose cross-village platform aggregates for any village_id. The mounted /api/v1/analytics is a per-user surface; this one has no caller identity at all.',
  },
  {
    file: 'services/workflow/main.py',
    reason:
      'not mountable: the APIRouter is constructed inside main(), which only runs under `python -m services.workflow.main` and serves its own app on port 8005. There is no module-level router to include; this is a separate deployable, not a gateway router.',
  },
  {
    file: 'services/api_gateway/routers/ecosystem.py',
    reason:
      'fabricated responses, not an auth problem: every handler returns a hardcoded constant (GET /activities returns [], GET /activities/{id} returns confidence 50 for any id, POST /activities/{id}/verify mints "eco_coin_minted": 500) and all four DI providers are `pass` stubs returning None. Mounting it would give a page catalogue 7 GETs that always render plausible fake data.',
  },
  {
    file: 'services/api_gateway/routers/lab.py',
    reason:
      'no auth: POST /api/mrv/lab/samples writes caller-supplied rows to disk under data/lab/ with no principal and no input sanitisation; GET reads them back.',
  },
  {
    file: 'services/telegram_bot/api/__init__.py',
    reason:
      'no auth: POST /telegram/notify relays an arbitrary message through the bot token (spam/abuse relay) and POST /telegram/webhook accepts unsigned updates.',
  },
  {
    file: 'services/marketplace/api/__init__.py',
    reason:
      'fabricated success: /api/v1/marketplace/health returns the constant {"status":"healthy"} with no dependency check. A page bound to it renders a permanent green state.',
  },
  {
    file: 'services/landscape/api/__init__.py',
    reason: 'fabricated success: /api/v1/landscape/health is the same constant liveness stub.',
  },
  {
    file: 'services/tourism/api/__init__.py',
    reason:
      'fabricated success: /api/v1/tourism/health is the same constant liveness stub. The honest module status is the mounted services/api_gateway/routers/tourism_router.py, which reports "requires_setup".',
  },
  {
    file: 'services/api_gateway/routers/admin.py',
    reason:
      'duplicate aggregator: it include_router()s the same eight admin_* modules main.py already mounts under /api/v1/admin, and its GET /health would be shadowed by the app-level /health declared in main.py itself.',
  },
  {
    file: 'services/auth/main.py',
    reason:
      'route collision: POST /api/v1/auth/register, POST /api/v1/auth/login and GET /api/v1/auth/me are already served by the mounted services/api_gateway/routers/auth.py. Mounting it would register three dead routes.',
  },
  {
    file: 'services/auth/api/__init__.py',
    reason:
      '0 GET and a second, unversioned /auth/login + /auth/register pair. The versioned, mounted services/api_gateway/routers/auth.py is the live surface.',
  },
  {
    file: 'services/bots/api/__init__.py',
    reason: '0 GET: write-only /bots/send|broadcast|advice. Bot administration is already mounted at /api/v1/admin/bots (require_admin_with_mfa).',
  },
  {
    file: 'services/satellite/api/__init__.py',
    reason: '0 GET: unversioned /satellite/monitor-field|detect-changes; the versioned services/api_gateway/routers/satellite.py is mounted.',
  },
  {
    file: 'services/api_gateway/routers/ai_advice_router.py',
    reason:
      '0 GET: write-only POST /api/v1/ai/advise, and unauthenticated LLM egress per request. No read contract for a page to bind to.',
  },
  {
    file: 'services/api_gateway/routers/climate.py',
    reason:
      '0 GET: write-only POST /api/v1/motors/{drought,climate,calibrate}, unauthenticated Open-Meteo egress per request. /motors/* is mounted from motors.py.',
  },
  {
    file: 'services/api_gateway/routers/economy.py',
    reason: '0 GET: write-only POST /api/motors/economy/, unauthenticated. The livelihood cost-benefit motor has no read contract.',
  },
];

/** Files that declare a router but are not part of the runtime surface. */
const WALK_SKIP_DIR = /(^|[\\/])(__pycache__|\.pytest_cache|node_modules)([\\/]|$)/;
const WALK_SKIP_FILE = /(^|[\\/])(tests?|__tests__)([\\/]|$)|(^|[\\/])(test_[^\\/]*|[^\\/]*_test|conftest)\.py$/;

// --------------------------------------------------------------------------- //
// filesystem helpers
// --------------------------------------------------------------------------- //

function walk(dir, acc = []) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return acc;
  }
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (WALK_SKIP_DIR.test(full)) continue;
    if (entry.isDirectory()) walk(full, acc);
    else if (entry.name.endsWith('.py')) acc.push(full);
  }
  return acc;
}

/** Dotted python module -> absolute .py file, or null. */
function moduleToFile(module) {
  const rel = module.split('.').join(sep);
  const candidates = [
    join(SERVICES, `${rel}.py`),
    join(SERVICES, rel, '__init__.py'),
    join(ROOT, `${rel}.py`),
    join(ROOT, rel, '__init__.py'),
  ];
  for (const c of candidates) if (existsSync(c)) return c;
  return null;
}

const pyPath = (file) => relative(ROOT, file).split(sep).join('/');

// --------------------------------------------------------------------------- //
// main.py: imports + include_router
// --------------------------------------------------------------------------- //

  /** `alias -> absolute file` for every `from X import (a, b as c)` in main.py. */
function parseMainAliases(text) {
  const aliases = new Map();
  // `from pkg import sub` where sub is a submodule resolves to pkg/sub.py;
  // `from pkg.mod import router` resolves to pkg/mod.py itself. Try the
  // submodule first, then fall back to the importing module.
  const target = (module, name) => {
    const asSubmodule = moduleToFile(resolveModule(`${module}.${name}`, ROOT_MAIN_PACKAGE));
    return asSubmodule || moduleToFile(resolveModule(module, ROOT_MAIN_PACKAGE));
  };
  const add = (module, names) => {
    for (const raw of names) {
      const piece = raw
        .replace(/#[^\n]*/g, '') // trailing comments on the `from` line
        .replace(/\r/g, '')
        .trim();
      if (!piece) continue;
      const m = piece.match(/^([A-Za-z_][\w]*)\s+as\s+([A-Za-z_][\w]*)$/);
      if (m) aliases.set(m[2], { module, file: target(module, m[1]), name: m[1] });
      else if (/^[A-Za-z_][\w]*$/.test(piece)) {
        aliases.set(piece, { module, file: target(module, piece), name: piece });
      }
    }
  };

  // parenthesised (possibly multi-line) form; a trailing comment may sit
  // between the module and `import`, e.g. `from .routers import (  # new`
  for (const m of text.matchAll(/^from\s+([.\w]+)[ \t]*(?:#[^\n]*)?[ \t\r\n]*import\s*\(([\s\S]*?)\)\s*$/gm)) {
    add(m[1], m[2].split(','));
  }
  // single-line form
  for (const m of text.matchAll(/^from\s+([.\w]+)\s+import\s+([^\n(]+?)\s*$/gm)) {
    add(m[1], m[2].split(','));
  }
  return aliases;
}

const ROOT_MAIN_PACKAGE = 'services.api_gateway';

/**
 * Resolve a possibly relative dotted import against the *package* of the file
 * that contains it. `basePackage` is the containing package, not the module:
 * `from .routers import x` inside services/api_gateway/main.py resolves against
 * `services.api_gateway`.
 */
function resolveModule(module, basePackage) {
  if (!module.startsWith('.')) return module;
  const level = module.length - module.replace(/^\.+/, '').length;
  const tail = module.replace(/^\.+/, '');
  const base = basePackage.split('.');
  // one leading dot == the current package, two == its parent, ...
  for (let i = 1; i < level; i += 1) base.pop();
  return tail ? [...base, ...tail.split('.')].join('.') : base.join('.');
}

/** Containing package (dotted) of a python file inside services/. */
function packageOf(file) {
  const rel = relative(SERVICES, file);
  const parts = rel.split(sep).filter(Boolean);
  if (parts[parts.length - 1] === '__init__.py') parts.pop();
  else parts.pop();
  return ['services', ...parts].join('.');
}

/** Balance-paren scan for `app.include_router(...)` call sites. */
function parseIncludeRouterCalls(text) {
  const calls = [];
  const re = /app\.include_router\s*\(/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const open = m.index + m[0].length - 1;
    let depth = 0;
    let i = open;
    for (; i < text.length; i += 1) {
      const ch = text[i];
      if (ch === '(') depth += 1;
      else if (ch === ')') {
        depth -= 1;
        if (depth === 0) break;
      }
    }
    const inner = text.slice(open + 1, i);
    const line = text.slice(0, m.index).split('\n').length;
    // first top-level argument
    let depth2 = 0;
    let split = inner.length;
    for (let j = 0; j < inner.length; j += 1) {
      const ch = inner[j];
      if ('([{'.includes(ch)) depth2 += 1;
      else if (')]}'.includes(ch)) depth2 -= 1;
      else if (ch === ',' && depth2 === 0) {
        split = j;
        break;
      }
    }
    const target = inner.slice(0, split).trim();
    const rest = inner.slice(split);
    const prefixM = rest.match(/\bprefix\s*=\s*(['"])(.*?)\1/);
    const tagsM = rest.match(/\btags\s*=\s*\[([^\]]*)\]/);
    calls.push({
      line,
      target,
      attribute: target.endsWith('.router') ? target.slice(0, -'.router'.length) : target,
      prefix: prefixM ? prefixM[2] : '',
      tags: tagsM ? tagsM[1] : '',
    });
  }
  return calls;
}

// --------------------------------------------------------------------------- //
// python file -> routers
// --------------------------------------------------------------------------- //

/** Strip comments and string bodies we must not match `@x.get(` inside. */
function stripNoise(text) {
  // remove triple-quoted blocks (docstrings) and # comments, preserving offsets
  let out = text;
  out = out.replace(/"""[\s\S]*?"""/g, (s) => s.replace(/[^\n]/g, ' '));
  out = out.replace(/'''[\s\S]*?'''/g, (s) => s.replace(/[^\n]/g, ' '));
  out = out.replace(/(^|[^:\\])#[^\n]*/g, (m, p1) => p1 + ' '.repeat(Math.max(0, m.length - p1.length)));
  return out;
}

/**
 * FastAPI composes a route path by literal concatenation:
 *   `APIRouter(prefix=...)` strips trailing slashes off the prefix, and
 * `include_router(prefix=...)` does the same, then `prefix + route.path`.
 * `/api/v1/models` + `""` is `/api/v1/models`, but `/analyses` + `"/"` really
 * is `/analyses/`. Collapsing the slash hides a distinct, live path, so the
 * concatenation is reproduced exactly here.
 */
function fastapiPath(...parts) {
  const out = parts
    .map((p, i) => (i === parts.length - 1 ? p || '' : (p || '').replace(/\/+$/, '')))
    .join('');
  return out === '' ? '/' : out;
}

const cache = new Map();

/** Balance-paren scan starting at `text[open]`; returns the index of the match. */
function matchParen(text, open) {
  let depth = 0;
  for (let i = open; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === '(') depth += 1;
    else if (ch === ')') {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  return -1;
}

/**
 * Analyse a python file: returns
 *   { file, routers: [{ var, prefix, routes: [{method, path}] }], shim: module|null }
 * `shim` is set when the file declares no APIRouter of its own but re-exports
 * one (`from a.b.c import router  # noqa: F401`).
 */
function analyseFile(file) {
  if (cache.has(file)) return cache.get(file);
  const raw = readFileSync(file, 'utf8');
  const text = stripNoise(raw);

  // every `NAME = APIRouter(` / `NAME: APIRouter = APIRouter(`, paren-balanced.
  // Python semantics: a later assignment to the same name replaces the earlier
  // one, so the map is keyed by variable and overwritten.
  const declMap = new Map();
  const declOrder = [];
  const declRe = /(^|\n)([ \t]*)([A-Za-z_]\w*)[ \t]*(?::[ \t]*[^=\n]+)?=[ \t]*APIRouter[ \t]*\(/g;
  let m;
  while ((m = declRe.exec(text)) !== null) {
    const open = m.index + m[0].length - 1;
    const close = matchParen(text, open);
    if (close === -1) continue;
    const args = text.slice(open + 1, close);
    const prefixM = args.match(/\bprefix\s*=\s*(['"])(.*?)\1/);
    // A declaration indented inside a function body is not a module attribute:
    // nothing can `include_router` it, it only exists while that function runs.
    const moduleLevel = m[2].length === 0;
    if (!declMap.has(m[3])) declOrder.push(m[3]);
    declMap.set(m[3], {
      var: m[3],
      prefix: prefixM ? prefixM[2] : '',
      duplicate: declMap.has(m[3]),
      moduleLevel,
    });
  }

  const routers = [];
  for (const varName of declOrder) {
    const d = declMap.get(varName);
    const routes = [];
    const re = new RegExp(`@${varName}\\.(?:(${HTTP_METHODS.join('|')})|api_route)\\s*\\(\\s*(['"])(.*?)\\2`, 'g');
    let dm;
    while ((dm = re.exec(text)) !== null) {
      routes.push({ method: dm[1] || 'api_route', path: dm[3] });
    }
    if (routes.length > 0) routers.push({ var: varName, prefix: d.prefix, routes, duplicateDecl: d.duplicate, moduleLevel: d.moduleLevel });
  }

  // sub-router includes inside a router file (router.include_router(sub, prefix=..))
  const nested = [];
  for (const n of text.matchAll(/([A-Za-z_]\w*)\.include_router\s*\(\s*([A-Za-z_]\w*)\s*(?:,\s*prefix\s*=\s*(['"])(.*?)\3)?/g)) {
    nested.push({ parent: n[1], child: n[2], prefix: n[4] || '' });
  }

  let shim = null;
  if (declMap.size === 0) {
    const shimM = text.match(/^from\s+([.\w]+)\s+import\s+router\b/m);
    if (shimM) shim = shimM[1];
  }

  const result = {
    file,
    routers,
    nested,
    shim,
    declaresRouter: declMap.size > 0,
    mountable: [...declMap.values()].some((d) => d.moduleLevel),
    duplicateRouters: declOrder.filter((v) => declMap.get(v).duplicate),
  };
  cache.set(file, result);
  return result;
}

/** Follow a shim chain to the file that actually owns the routes. */
function resolveShim(file, seen = new Set()) {
  if (seen.has(file)) return { file: null, chain: [...seen] };
  seen.add(file);
  const info = analyseFile(file);
  // a router with zero routes is still a valid mount target (an empty stub)
  if (info.declaresRouter && info.mountable) return { file, chain: [...seen] };
  if (!info.shim) return { file: null, chain: [...seen] };
  const base = packageOf(file);
  const target = moduleToFile(resolveModule(info.shim, base));
  if (!target) return { file: null, chain: [...seen] };
  return resolveShim(target, seen);
}

// --------------------------------------------------------------------------- //
// build
// --------------------------------------------------------------------------- //

const mainText = readFileSync(MAIN, 'utf8');
const aliases = parseMainAliases(mainText);
const calls = parseIncludeRouterCalls(mainText);

const mounted = []; // { method, path, owner, via, line, prefix, routerPrefix }
const mountErrors = [];
const unresolvable = [];

for (const call of calls) {
  const target = aliases.get(call.attribute);
  if (!target || !target.file) {
    unresolvable.push({ line: call.line, target: call.attribute, reason: target ? 'module not found' : 'no matching import alias' });
    continue;
  }
  const { file: owner, chain } = resolveShim(target.file);
  if (!owner) {
    unresolvable.push({ line: call.line, target: call.attribute, reason: `resolved to ${pyPath(target.file)} which declares no router and has no shim` });
    continue;
  }
  const info = analyseFile(owner);
  const hopCount = chain.length - 1;
  for (const r of info.routers) {
    for (const route of r.routes) {
      if (route.method === 'api_route') continue;
      mounted.push({
        method: route.method.toUpperCase(),
        path: fastapiPath(call.prefix, r.prefix, route.path),
        owner: pyPath(owner),
        via: pyPath(target.file),
        shimHops: hopCount,
        line: call.line,
      });
    }
  }
}

// every router-declaring file under services/
const allFiles = walk(SERVICES);
const declaredByFile = new Map(); // ownerFile -> [{method, path, routerVar, routerPrefix}]
for (const file of allFiles) {
  if (WALK_SKIP_FILE.test(file)) continue;
  const info = analyseFile(file);
  if (info.routers.length === 0) continue;
  const routes = [];
  for (const r of info.routers) {
    for (const route of r.routes) {
      if (route.method === 'api_route') continue;
      routes.push({
        method: route.method.toUpperCase(),
        path: fastapiPath(r.prefix, route.path),
        routerVar: r.var,
        routerPrefix: r.prefix,
      });
    }
  }
  if (routes.length > 0) declaredByFile.set(file, routes);
}

const mountedKeys = new Set(mounted.map((m) => `${m.method} ${m.path}`));
const mountedOwners = new Set(mounted.map((m) => m.owner));

const exclusionByFile = new Map(EXCLUSIONS.map((e) => [e.file, e.reason]));

// a declared file is "mounted" if any of its routes got mounted under some prefix,
// or if it is a shim target reached through an include_router
const shimTargets = new Set();
for (const call of calls) {
  const t = aliases.get(call.attribute);
  if (t && t.file) {
    const r = resolveShim(t.file);
    if (r.file) shimTargets.add(pyPath(r.file));
  }
}

const unmountedFiles = [];
for (const [file, routes] of [...declaredByFile.entries()].sort()) {
  const rel = pyPath(file);
  if (mountedOwners.has(rel) || shimTargets.has(rel)) continue;
  unmountedFiles.push({ file: rel, routes, excluded: exclusionByFile.get(rel) || null });
}
const unlisted = unmountedFiles.filter((u) => !u.excluded);
const listed = unmountedFiles.filter((u) => u.excluded);

// stale exclusions: listed but no longer unmounted
const staleExclusions = EXCLUSIONS.filter((e) => !unmountedFiles.some((u) => u.file === e.file));

// per-method summary
const byMethod = {};
for (const method of HTTP_METHODS.map((m) => m.toUpperCase())) {
  const m = new Set(mounted.filter((r) => r.method === method).map((r) => r.path));
  const declared = new Set();
  for (const [, routes] of declaredByFile) {
    for (const r of routes) if (r.method === method) declared.add(r.path);
  }
  byMethod[method] = { mounted: m.size, declared: declared.size };
}

// collisions: same METHOD+path mounted more than once
const seenPath = new Map();
for (const m of mounted) {
  const key = `${m.method} ${m.path}`;
  if (!seenPath.has(key)) seenPath.set(key, []);
  seenPath.get(key).push(m);
}
const collisions = [...seenPath.entries()]
  .filter(([, list]) => list.length > 1)
  .map(([key, list]) => ({
    key,
    winner: list[0], // app.routes is first-match-wins
    shadowed: list.slice(1),
  }));

// --------------------------------------------------------------------------- //
// batch plan
//
// `--plan` answers, for every unmounted router file, what paths mounting it at
// its own declared prefix would add and which of them are already served by a
// mounted router. Run it before every batch: mounting is a shared global
// table, so a duplicate METHOD+path means the later registration is dead.
// --------------------------------------------------------------------------- //

function buildPlan() {
  const mountedKeys = new Map(); // "METHOD path" -> { owner, line }
  for (const m of mounted) {
    if (!mountedKeys.has(`${m.method} ${m.path}`)) mountedKeys.set(`${m.method} ${m.path}`, m);
  }
  return unmountedFiles.map((u) => {
    const wouldAdd = u.routes.map((r) => `${r.method} ${r.path}`);
    const clashes = wouldAdd.map((key) => ({ key, existing: mountedKeys.get(key) || null }));
    return {
      file: u.file,
      get: u.routes.filter((r) => r.method === 'GET').length,
      ops: u.routes.length,
      excluded: u.excluded,
      clashes: clashes.filter((c) => c.existing),
      routes: wouldAdd,
    };
  });
}

// --------------------------------------------------------------------------- //
// optional runtime cross-check
//
// `--verify-runtime <file.json>` diffs the static result against a dump of the
// real `app.openapi()` document, which is the only source that reflects
// FastAPI's first-match-wins resolution. The static analysis is a convenience;
// the runtime dump is the proof that it is not lying.
// --------------------------------------------------------------------------- //

function verifyRuntime(file) {
  if (!existsSync(file)) {
    console.log(`runtime dump not found: ${file}`);
    return { checked: false };
  }
  // The app-level endpoints in main.py (`/`, `/health`, ...) and the
  // prometheus `/metrics` endpoint are not declared in a router file, so the
  // static walk cannot know about them.
  const APP_LEVEL = new Set(['GET /', 'GET /health', 'GET /health/live', 'GET /health/ready', 'GET /api/v1/health', 'GET /ready', 'GET /metrics', 'POST /', 'POST /health']);
  // OpenAPI renders `{param:convertor}` as `{param}`; compare on that form.
  const norm = (p) => p.replace(/\{([A-Za-z_]\w*):[A-Za-z_]\w*\}/g, '{$1}');
  const dump = JSON.parse(readFileSync(file, 'utf8'));
  const staticKeys = new Set(mounted.map((m) => `${m.method} ${norm(m.path)}`));
  const missingInStatic = [];
  const extraInStatic = [];
  let runtimeOps = 0;
  for (const [method, paths] of Object.entries(dump)) {
    for (const p of paths) {
      runtimeOps += 1;
      if (APP_LEVEL.has(`${method} ${p}`)) continue;
      if (!staticKeys.has(`${method} ${norm(p)}`)) missingInStatic.push(`${method} ${p}`);
    }
  }
  for (const key of staticKeys) {
    if (!dump[key.split(' ')[0]]?.includes(key.slice(key.indexOf(' ') + 1))) extraInStatic.push(key);
  }
  return { checked: true, runtimeOps, staticOps: staticKeys.size, missingInStatic, extraInStatic };
}

const runtimeIdx = process.argv.indexOf('--verify-runtime');
const runtime = runtimeIdx !== -1 ? verifyRuntime(process.argv[runtimeIdx + 1]) : { checked: false };

// --------------------------------------------------------------------------- //
// report
// --------------------------------------------------------------------------- //

const totalMountedOps = mounted.length;
const mountedGet = byMethod.GET.mounted;
const declaredGet = byMethod.GET.declared;

if (process.argv.includes('--json')) {
  process.stdout.write(
    JSON.stringify(
      {
        routersIncluded: calls.length,
        mountedOperations: totalMountedOps,
        byMethod: Object.fromEntries(Object.entries(byMethod).map(([k, v]) => [k, v.mounted])),
        declaredGet,
        mountedGet,
        unreachableGet: declaredGet - mountedGet,
        unresolvableMounts: unresolvable,
        collisions: collisions.map((c) => ({ key: c.key, winner: c.winner.owner, shadowed: c.shadowed.map((s) => s.owner) })),
        unmounted: unlisted.map((u) => ({ file: u.file, get: u.routes.filter((r) => r.method === 'GET').length, ops: u.routes.length })),
        exclusions: EXCLUSIONS,
        staleExclusions,
        missingExclusionReasons: listed.filter((u) => !u.excluded).map((u) => u.file),
        plan: process.argv.includes('--plan') ? buildPlan() : undefined,
        runtime,
      },
      null,
      2,
    ),
  );
  process.exit(unresolvable.length || unlisted.length || collisions.length ? 1 : 0);
}

const quiet = process.argv.includes('--quiet');
if (!quiet) {
  console.log('=== MOUNTED ROUTE INVENTORY ===');
  console.log(`service packages under services/ : ${new Set(allFiles.map((f) => f.split(sep)[3]).filter(Boolean)).size}`);
  console.log(`routers included in main.py        : ${calls.length}`);
  console.log(`mounted operations                : ${totalMountedOps}`);
  for (const method of HTTP_METHODS.map((m) => m.toUpperCase())) {
    console.log(`  - ${method.padEnd(6)} : ${byMethod[method].mounted}`);
  }
  console.log(`GET declared anywhere under services/ : ${declaredGet}`);
  console.log(`GET reachable                          : ${mountedGet}`);
  console.log(`GET unreachable                       : ${Math.max(0, declaredGet - mountedGet)}`);
  console.log('');
  console.log(`unresolvable include_router targets: ${unresolvable.length}`);
  for (const u of unresolvable) console.log(`  main.py:${u.line}  ${u.target}  -- ${u.reason}`);
  console.log('');
  console.log(`path collisions (first match wins): ${collisions.length}`);
  for (const c of collisions) {
    console.log(`  ${c.key}`);
    console.log(`      WINS     : ${c.winner.owner} (main.py:${c.winner.line})`);
    for (const s of c.shadowed) console.log(`      SHADOWED : ${s.owner} (main.py:${s.line})`);
  }
  console.log('');
  console.log(`--- routers declaring routes but not mounted (${unmountedFiles.length}) ---`);
  for (const u of unmountedFiles) {
    const get = u.routes.filter((r) => r.method === 'GET').length;
    const ops = u.routes.length;
    const mark = u.excluded ? `  [EXCLUDED: ${u.excluded}]` : '  [UNMAPPED]';
    console.log(`  ${u.file}  ops=${ops} get=${get}${mark}`);
    for (const r of u.routes) console.log(`        ${r.method.padEnd(6)} ${r.path}`);
  }
  console.log('');
  console.log(`--- EXCLUSIONS (${EXCLUSIONS.length}) ---`);
  if (EXCLUSIONS.length === 0) console.log('  (none declared)');
  for (const e of EXCLUSIONS) console.log(`  ${e.file}\n      reason: ${e.reason}`);
  if (staleExclusions.length) {
    console.log('');
    console.log('  !! STALE EXCLUSIONS (no longer unmounted; remove them):');
    for (const e of staleExclusions) console.log(`     ${e.file}`);
  }
  if (process.argv.includes('--plan')) {
    const plan = buildPlan();
    console.log('');
    console.log('--- MOUNT PLAN: paths each unmounted router would add at its own prefix ---');
    for (const p of plan) {
      const flag = p.clashes.length ? `  !! ${p.clashes.length} COLLISION(S)` : '';
      console.log(`  ${p.file}  get=${p.get} ops=${p.ops}${flag}`);
      for (const c of p.clashes) {
        console.log(`        ${c.key}`);
        console.log(`            already served by ${c.existing.owner} (main.py:${c.existing.line})`);
      }
    }
  }
  if (runtime.checked) {
    console.log('');
    console.log(`--- RUNTIME CROSS-CHECK (app.openapi() dump) ---`);
    console.log(`  runtime ops: ${runtime.runtimeOps}   static ops: ${runtime.staticOps}`);
    console.log(`  in app but not matched statically: ${runtime.missingInStatic.length}`);
    for (const k of runtime.missingInStatic) console.log(`      ${k}`);
    console.log(`  matched statically but not in app: ${runtime.extraInStatic.length}`);
    for (const k of runtime.extraInStatic) console.log(`      ${k}`);
  }
}

if (unresolvable.length) {
  console.log(`\nFAIL: ${unresolvable.length} include_router() target(s) cannot be resolved.`);
}
if (collisions.length) {
  console.log(`\nFAIL: ${collisions.length} duplicate METHOD+path registration(s) -- the later one is unreachable.`);
}
if (unlisted.length) {
  const gets = unlisted.reduce((n, u) => n + u.routes.filter((r) => r.method === 'GET').length, 0);
  console.log(
    `\nFAIL: ${unlisted.length} router(s) under services/ declare ${gets} GET route(s) and are not mounted and are not on the exclusion list.`,
  );
}
if (unresolvable.length || collisions.length || unlisted.length) process.exit(1);
console.log('\nOK -- every declared router is either mounted or explicitly excluded.');
