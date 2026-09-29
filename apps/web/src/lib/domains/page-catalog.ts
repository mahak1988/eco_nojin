import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Page catalog — the single registry of the 600 logical frontend paths.
 *
 * GENERATED FILE. Every field is derived from a real artefact in this
 * repository: a route file under `apps/web/src/app/[locale]`, the scientific
 * tool registry, the marketplace route plan, or a contract published in
 * `openapi.json` / `services/api_gateway/routers/*.py`. No endpoint, metric or
 * capability is invented here.
 *
 * Status is resolved by one rule, and the rule is enforced by the colocated
 * test so a page can never claim more than the repository proves:
 *
 *   endpoint === null                       -> 'unavailable' (noindex)
 *   endpoint === null + declared content     -> 'static'      (index)
 *   endpoint + concrete route file          -> 'live'         (index)
 *   endpoint + registry-driven route file   -> 'capability'   (index)
 *   endpoint + no route file yet            -> 'planned'      (noindex)
 *
 * `live` is a concrete route file; `capability` is a route that resolves from
 * a registry (a dynamic segment backed by a real engine or gateway registry).
 * A surface the gateway does not publish can never be indexed: `unavailable`
 * and `planned` are both noindex, so a page stays out of search results until
 * a contract is registered for it.
 */

export const PAGE_CATALOG_VERSION = '2026-09-26';
export const PAGE_CATALOG_TOTAL = 600;

export const CATALOG_DOMAINS = [
  'public',
  'marketplace',
  'hydroma',
  'admin',
  'research',
  'system',
  'workspace',
  'inclusive',
  'learning',
] as const;

export type CatalogDomain = (typeof CATALOG_DOMAINS)[number];

export const CATALOG_STATUSES = ['live', 'capability', 'static', 'planned', 'unavailable'] as const;

export type CatalogStatus = (typeof CATALOG_STATUSES)[number];

export const CATALOG_ACCESSES = ['public', 'authenticated', 'role-gated', 'internal'] as const;

export type CatalogAccess = (typeof CATALOG_ACCESSES)[number];

export interface CatalogEntry {
  id: string;
  path: string;
  domain: CatalogDomain;
  status: CatalogStatus;
  /** Real gateway contract, or `null` while the web layer has none. */
  endpoint: string | null;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Repository file that decides what this surface may show. */
  sourceOfTruth: string;
  owner: string;
  gate: string;
  access: CatalogAccess;
  /** Existing route that owns this path, when the path is already routed. */
  routeFile: string | null;
  /** Who renders the path: a real page, the marketplace catch-all or this catalog. */
  renderedBy: 'route' | 'marketplace-catchall' | 'catalog-catchall';
  indexable: boolean;
  description: string;
}

interface CatalogSeed {
  id: string;
  domain: CatalogDomain;
  path: string;
  status: CatalogStatus;
  endpoint: string | null;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  sourceOfTruth: string;
  routeFile: string | null;
  /**
   * Overrides the group's access label where the published contract disagrees
   * with the team that owns the surface.
   */
  access?: CatalogAccess;
  description: string;
}

/**
 * Repository root, found by walking up until a known marker is present.
 *
 * Counting `..` segments is what made this wrong twice — the path is five levels
 * up, not four, and a wrong root turns every `routeFile` lookup into a silent
 * miss, which then reads as "no page exists" for all 600 entries. A walk cannot
 * be off by one, and it fails loudly if the layout changes.
 */
const REPO_ROOT = (() => {
  let current = dirname(fileURLToPath(import.meta.url));
  for (let depth = 0; depth < 12; depth += 1) {
    if (existsSync(join(current, 'openapi.json'))) return current;
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..', '..');
})();

/**
 * Static public surfaces: content that is not an API resource.
 *
 * `docs/frontend/contract-allowlist.json` is the single written decision that a
 * path is content rather than a contract-less endpoint. Reading it here keeps
 * that decision and the catalogue in step: a path may be indexable without a
 * gateway contract only while the allowlist says so.
 */
const DECLARED_STATIC: { routes: ReadonlySet<string>; prefixes: readonly string[] } = (() => {
  try {
    const raw = readFileSync(
      join(REPO_ROOT, 'docs', 'frontend', 'contract-allowlist.json'),
      'utf8',
    );
    const parsed = JSON.parse(raw) as {
      declaredContent?: Array<{ path?: string }>;
      declaredStaticRoutes?: string[];
      declaredStaticPrefixes?: string[];
    };
    const routes = new Set<string>(
      [
        ...(parsed.declaredStaticRoutes ?? []),
        ...(parsed.declaredContent ?? []).map((entry) => entry.path ?? ''),
      ].filter((path) => path),
    );
    return { routes, prefixes: parsed.declaredStaticPrefixes ?? [] };
  } catch {
    return { routes: new Set<string>(), prefixes: [] };
  }
})();

function isDeclaredStatic(path: string): boolean {
  if (DECLARED_STATIC.routes.has(path)) return true;
  return DECLARED_STATIC.prefixes.some((prefix) => path.startsWith(prefix));
}

/** Owner, gate, access and landing page per group, from the real route manifest. */
export const CATALOG_GROUPS = [
  {
    domain: 'public',
    owner: 'content-platform',
    gate: 'metadata+a11y+i18n',
    access: 'public',
    landing: '/about',
  },
  {
    domain: 'marketplace',
    owner: 'marketplace',
    gate: 'contract+escrow+auth+e2e+security',
    access: 'public',
    landing: '/market',
  },
  {
    domain: 'hydroma',
    owner: 'hydroma',
    gate: 'schema+replay+provenance+performance+e2e',
    access: 'public',
    landing: '/hydroma',
  },
  {
    domain: 'admin',
    owner: 'platform-admin',
    gate: 'authz+audit+security+e2e',
    access: 'role-gated',
    landing: '/admin',
  },
  {
    domain: 'research',
    owner: 'research-platform',
    gate: 'authz+reproducibility+contract+e2e',
    access: 'authenticated',
    landing: '/research',
  },
  {
    domain: 'system',
    owner: 'platform-operations',
    gate: 'health+security+telemetry+e2e',
    access: 'internal',
    landing: '/system',
  },
  {
    domain: 'workspace',
    owner: 'platform-operations',
    gate: 'authz+contract+e2e',
    access: 'role-gated',
    landing: '/workspace',
  },
  {
    domain: 'inclusive',
    owner: 'platform-operations',
    gate: 'channel-contract+e2e',
    access: 'public',
    landing: '/simple',
  },
  {
    domain: 'learning',
    owner: 'content-platform',
    gate: 'content-review+i18n+a11y',
    access: 'public',
    landing: '/learn',
  },
] as const satisfies readonly {
  domain: CatalogDomain;
  owner: string;
  gate: string;
  access: CatalogAccess;
  landing: string;
}[];

/** `/market` is already owned by the marketplace catch-all route. */
export const RESERVED_CATCH_ALL_PREFIXES = ['/market'] as const;

/**
 * Routes on disk that no catalogue entry claims.
 *
 * The catalogue is meant to be the single inventory of the product, so a page
 * that exists without an entry is a gap. These four predate the catalogue and
 * are declared rather than added, because each is a duplicate of a surface that
 * *is* catalogued under a different path, and the reason is recorded per entry so
 * the declaration cannot quietly become a dumping ground.
 *
 * `page-catalog.test.ts` asserts the list equals the computed difference, in both
 * directions, so any further stray page fails the suite.
 */
export const OUT_OF_CATALOGUE_ROUTES: readonly {
  routeFile: string;
  path: string;
  reason: string;
}[] = [
  {
    routeFile: 'apps/web/src/app/[locale]/design-system/components/page.tsx',
    path: '/design-system/components',
    reason:
      'A browsable gallery of the primitives at every density and every required state. It is a team reference rather than a product surface: noindex, and outside the catalogue on purpose so it is not counted as inventory.',
  },
  {
    routeFile: 'apps/web/src/app/[locale]/admin/system/health/page.tsx',
    path: '/admin/system/health',
    reason:
      'Operational health for administrators. The catalogue publishes /system/health for the same gateway read; this path is the role-gated alias.',
  },
  {
    routeFile: 'apps/web/src/app/[locale]/workspace/operations/health/page.tsx',
    path: '/workspace/operations/health',
    reason:
      'Workspace-scoped health. The catalogue publishes /system/health for the same gateway read; this path resolves the tenant.',
  },
  {
    routeFile: 'apps/web/src/app/[locale]/developers/api/page.tsx',
    path: '/developers/api',
    reason:
      'API reference. The catalogue publishes /developers for the developer surface; this path is the OpenAPI reference alias.',
  },
];

export function isReservedPath(path: string): boolean {
  return RESERVED_CATCH_ALL_PREFIXES.some(
    (prefix) => path === prefix || path.startsWith(`${prefix}/`),
  );
}

/**
 * The only place a status is decided. Keeping it pure lets the colocated test
 * prove the rule for all 600 entries instead of trusting the literals.
 */
export function resolveCatalogStatus(input: {
  endpoint: string | null;
  hasRoute: boolean;
  registryDriven: boolean;
  declaredContent?: boolean;
}): CatalogStatus {
  if (input.endpoint === null) {
    if (input.hasRoute && input.declaredContent === true) return 'static';
    return 'unavailable';
  }
  if (input.hasRoute) return input.registryDriven ? 'capability' : 'live';
  return 'planned';
}

/**
 * A live route backed by a published contract may be indexed, and so may a
 * declared content surface; every other state is noindex.
 */
export function resolveIndexable(status: CatalogStatus): boolean {
  return status === 'live' || status === 'capability' || status === 'static';
}

export function resolveRobots(status: CatalogStatus): {
  index: boolean;
  follow: boolean;
} {
  return { index: resolveIndexable(status), follow: resolveIndexable(status) };
}

const SEEDS: readonly CatalogSeed[] = [
  {
    id: 'public-',
    domain: 'public',
    path: '/',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/page.tsx',
    description:
      'Registered surface /. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/page.tsx.',
  },
  {
    id: 'public-about',
    domain: 'public',
    path: '/about',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/about/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/about/page.tsx',
    description:
      'Registered surface /about. No gateway contract is published for it; apps/web/src/app/[locale]/about/page.tsx is the only source of truth.',
  },
  {
    id: 'public-ai',
    domain: 'public',
    path: '/ai',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/page.tsx',
    description:
      'Registered surface /ai. No gateway contract is published for it; apps/web/src/app/[locale]/ai/page.tsx is the only source of truth.',
  },
  {
    id: 'public-ai-agents',
    domain: 'public',
    path: '/ai/agents',
    status: 'live',
    endpoint: '/api/v1/ai/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/agents/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/agents/page.tsx',
    description:
      'Registered surface /ai/agents. Gateway contract: GET /api/v1/ai/health, registered in apps/web/src/app/[locale]/ai/agents/page.tsx.',
  },
  {
    id: 'public-ai-analysis-advise',
    domain: 'public',
    path: '/ai/analysis/advise',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/advise',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/advise. Gateway contract: POST /api/v1/ai/analysis/advise, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-analysis-drought',
    domain: 'public',
    path: '/ai/analysis/drought',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/drought',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/drought. Gateway contract: POST /api/v1/ai/analysis/drought, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-analysis-drought-report',
    domain: 'public',
    path: '/ai/analysis/drought-report',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/drought-report',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/drought-report. Gateway contract: POST /api/v1/ai/analysis/drought-report, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-analysis-providers',
    domain: 'public',
    path: '/ai/analysis/providers',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/providers',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/providers. Gateway contract: GET /api/v1/ai/analysis/providers, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-analysis-scenario',
    domain: 'public',
    path: '/ai/analysis/scenario',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/scenario',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/scenario. Gateway contract: POST /api/v1/ai/analysis/scenario, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-analysis-scenarios',
    domain: 'public',
    path: '/ai/analysis/scenarios',
    status: 'planned',
    endpoint: '/api/v1/ai/analysis/scenarios',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_analysis.py',
    routeFile: null,
    description:
      'Registered surface /ai/analysis/scenarios. Gateway contract: POST /api/v1/ai/analysis/scenarios, registered in services/api_gateway/routers/ai_analysis.py.',
  },
  {
    id: 'public-ai-assistant',
    domain: 'public',
    path: '/ai/assistant',
    status: 'live',
    endpoint: '/api/v1/ai/chat',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/assistant/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/assistant/page.tsx',
    description:
      'Registered surface /ai/assistant. Gateway contract: GET /api/v1/ai/chat, registered in apps/web/src/app/[locale]/ai/assistant/page.tsx.',
  },
  {
    id: 'public-ai-chat',
    domain: 'public',
    path: '/ai/chat',
    status: 'planned',
    endpoint: '/api/v1/ai/chat',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai.py',
    routeFile: null,
    description:
      'Registered surface /ai/chat. Gateway contract: POST /api/v1/ai/chat, registered in services/api_gateway/routers/ai.py.',
  },
  {
    id: 'public-ai-ethics',
    domain: 'public',
    path: '/ai/ethics',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/ethics/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/ethics/page.tsx',
    description:
      'Registered surface /ai/ethics. No gateway contract is published for it; apps/web/src/app/[locale]/ai/ethics/page.tsx is the only source of truth.',
  },
  {
    id: 'public-ai-feedback',
    domain: 'public',
    path: '/ai/feedback',
    status: 'live',
    endpoint: '/api/v1/contact',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/feedback/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/feedback/page.tsx',
    description:
      'Registered surface /ai/feedback. Gateway contract: GET /api/v1/contact, registered in apps/web/src/app/[locale]/ai/feedback/page.tsx.',
  },
  {
    id: 'public-ai-glossary',
    domain: 'public',
    path: '/ai/glossary',
    status: 'live',
    endpoint: '/api/v1/science/agrovoc',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/glossary/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/glossary/page.tsx',
    description:
      'Registered surface /ai/glossary. Gateway contract: GET /api/v1/science/agrovoc, registered in apps/web/src/app/[locale]/ai/glossary/page.tsx.',
  },
  {
    id: 'public-ai-health',
    domain: 'public',
    path: '/ai/health',
    status: 'planned',
    endpoint: '/api/v1/ai/health',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/ai.py',
    routeFile: null,
    description:
      'Registered surface /ai/health. Gateway contract: GET /api/v1/ai/health, registered in services/api_gateway/routers/ai.py.',
  },
  {
    id: 'public-ai-history',
    domain: 'public',
    path: '/ai/history',
    status: 'planned',
    endpoint: '/api/v1/ai/history',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/ai_chat.py',
    routeFile: null,
    description:
      'Registered surface /ai/history. Gateway contract: GET /api/v1/ai/history, registered in services/api_gateway/routers/ai_chat.py.',
  },
  {
    id: 'public-ai-limits',
    domain: 'public',
    path: '/ai/limits',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/limits/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/limits/page.tsx',
    description:
      'Registered surface /ai/limits. No gateway contract is published for it; apps/web/src/app/[locale]/ai/limits/page.tsx is the only source of truth.',
  },
  {
    id: 'public-ai-stream',
    domain: 'public',
    path: '/ai/stream',
    status: 'planned',
    endpoint: '/api/v1/ai/stream',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_chat.py',
    routeFile: null,
    description:
      'Registered surface /ai/stream. Gateway contract: POST /api/v1/ai/stream, registered in services/api_gateway/routers/ai_chat.py.',
  },
  {
    id: 'public-ai-voice',
    domain: 'public',
    path: '/ai/voice',
    status: 'live',
    endpoint: '/api/v1/ai/chat',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/ai/voice/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/ai/voice/page.tsx',
    description:
      'Registered surface /ai/voice. Gateway contract: GET /api/v1/ai/chat, registered in apps/web/src/app/[locale]/ai/voice/page.tsx.',
  },
  {
    id: 'public-ai-voice-tts',
    domain: 'public',
    path: '/ai/voice/tts',
    status: 'planned',
    endpoint: '/api/v1/ai/voice/tts',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/ai_chat.py',
    routeFile: null,
    description:
      'Registered surface /ai/voice/tts. Gateway contract: POST /api/v1/ai/voice/tts, registered in services/api_gateway/routers/ai_chat.py.',
  },
  {
    id: 'public-design-system',
    domain: 'public',
    path: '/design-system',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/design-system/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/design-system/page.tsx',
    description:
      'Registered surface /design-system. No gateway contract is published for it; apps/web/src/app/[locale]/design-system/page.tsx is the only source of truth.',
  },
  {
    id: 'public-developers',
    domain: 'public',
    path: '/developers',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/page.tsx',
    description:
      'Registered surface /developers. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/developers/page.tsx.',
  },
  {
    id: 'public-developers-changelog',
    domain: 'public',
    path: '/developers/changelog',
    status: 'live',
    endpoint: '/api/v1/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/changelog/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/changelog/page.tsx',
    description:
      'Registered surface /developers/changelog. Gateway contract: GET /api/v1/health, registered in apps/web/src/app/[locale]/developers/changelog/page.tsx.',
  },
  {
    id: 'public-developers-cookbooks',
    domain: 'public',
    path: '/developers/cookbooks',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/cookbooks/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/cookbooks/page.tsx',
    description:
      'Registered surface /developers/cookbooks. No gateway contract is published for it; apps/web/src/app/[locale]/developers/cookbooks/page.tsx is the only source of truth.',
  },
  {
    id: 'public-developers-partners',
    domain: 'public',
    path: '/developers/partners',
    status: 'live',
    endpoint: '/api/v1/organizations',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/partners/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/partners/page.tsx',
    description:
      'Registered surface /developers/partners. Gateway contract: GET /api/v1/organizations, registered in apps/web/src/app/[locale]/developers/partners/page.tsx.',
  },
  {
    id: 'public-developers-playground',
    domain: 'public',
    path: '/developers/playground',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/playground/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/playground/page.tsx',
    description:
      'Registered surface /developers/playground. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/developers/playground/page.tsx.',
  },
  {
    id: 'public-developers-sdks',
    domain: 'public',
    path: '/developers/sdks',
    status: 'live',
    endpoint: '/api/v1/tool-registry',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/sdks/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/sdks/page.tsx',
    description:
      'Registered surface /developers/sdks. Gateway contract: GET /api/v1/tool-registry, registered in apps/web/src/app/[locale]/developers/sdks/page.tsx.',
  },
  {
    id: 'public-developers-status-api',
    domain: 'public',
    path: '/developers/status-api',
    status: 'live',
    endpoint: '/api/v1/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/status-api/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/status-api/page.tsx',
    description:
      'Registered surface /developers/status-api. Gateway contract: GET /api/v1/health, registered in apps/web/src/app/[locale]/developers/status-api/page.tsx.',
  },
  {
    id: 'public-developers-webhooks',
    domain: 'public',
    path: '/developers/webhooks',
    status: 'live',
    endpoint: '/api/v1/mrv/lorawan-webhook',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/developers/webhooks/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/developers/webhooks/page.tsx',
    description:
      'Registered surface /developers/webhooks. Gateway contract: GET /api/v1/mrv/lorawan-webhook, registered in apps/web/src/app/[locale]/developers/webhooks/page.tsx.',
  },
  {
    id: 'public-evidence',
    domain: 'public',
    path: '/evidence',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/evidence/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/evidence/page.tsx',
    description:
      'Registered surface /evidence. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/evidence/page.tsx.',
  },
  {
    id: 'public-help-chat',
    domain: 'public',
    path: '/help/chat',
    status: 'planned',
    endpoint: '/api/v1/support/chat',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/support.py',
    routeFile: null,
    description:
      'Registered surface /help/chat. Gateway contract: POST /api/v1/support/chat, registered in services/api_gateway/routers/support.py.',
  },
  {
    id: 'public-help-contact',
    domain: 'public',
    path: '/help/contact',
    status: 'planned',
    endpoint: '/api/v1/contact',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /help/contact. Gateway contract: POST /api/v1/contact, registered in openapi.json.',
  },
  {
    id: 'public-help-personas',
    domain: 'public',
    path: '/help/personas',
    status: 'planned',
    endpoint: '/api/v1/support/personas',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/support.py',
    routeFile: null,
    description:
      'Registered surface /help/personas. Gateway contract: GET /api/v1/support/personas, registered in services/api_gateway/routers/support.py.',
  },
  {
    id: 'public-home',
    domain: 'public',
    path: '/home',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/home/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/home/page.tsx',
    description:
      'Registered surface /home. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/home/page.tsx.',
  },
  {
    id: 'public-legal',
    domain: 'public',
    path: '/legal',
    status: 'live',
    endpoint: '/api/v1/legal-texts',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/legal/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/legal/page.tsx',
    description:
      'Registered surface /legal. Gateway contract: GET /api/v1/legal-texts, registered in apps/web/src/app/[locale]/legal/page.tsx.',
  },
  {
    id: 'public-platform',
    domain: 'public',
    path: '/platform',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/platform/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/platform/page.tsx',
    description:
      'Registered surface /platform. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/platform/page.tsx.',
  },
  {
    id: 'public-prototype',
    domain: 'public',
    path: '/prototype',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/prototype/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/prototype/page.tsx',
    description:
      'Registered surface /prototype. No gateway contract is published for it; apps/web/src/app/[locale]/prototype/page.tsx is the only source of truth.',
  },
  {
    id: 'public-public-audiences-cooperatives',
    domain: 'public',
    path: '/public/audiences/cooperatives',
    status: 'live',
    endpoint: '/api/v1/marketplace/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/cooperatives/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/cooperatives/page.tsx',
    description:
      'Registered surface /public/audiences/cooperatives. Gateway contract: GET /api/v1/marketplace/stats, registered in apps/web/src/app/[locale]/public/audiences/cooperatives/page.tsx.',
  },
  {
    id: 'public-public-audiences-farmers',
    domain: 'public',
    path: '/public/audiences/farmers',
    status: 'live',
    endpoint: '/api/v1/land/profiles',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/farmers/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/farmers/page.tsx',
    description:
      'Registered surface /public/audiences/farmers. Gateway contract: GET /api/v1/land/profiles, registered in apps/web/src/app/[locale]/public/audiences/farmers/page.tsx.',
  },
  {
    id: 'public-public-audiences-government',
    domain: 'public',
    path: '/public/audiences/government',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/government/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/government/page.tsx',
    description:
      'Registered surface /public/audiences/government. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/public/audiences/government/page.tsx.',
  },
  {
    id: 'public-public-audiences-investors',
    domain: 'public',
    path: '/public/audiences/investors',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/investors/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/investors/page.tsx',
    description:
      'Registered surface /public/audiences/investors. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/public/audiences/investors/page.tsx.',
  },
  {
    id: 'public-public-audiences-ngos',
    domain: 'public',
    path: '/public/audiences/ngos',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/ngos/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/ngos/page.tsx',
    description:
      'Registered surface /public/audiences/ngos. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/public/audiences/ngos/page.tsx.',
  },
  {
    id: 'public-public-audiences-researchers',
    domain: 'public',
    path: '/public/audiences/researchers',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/audiences/researchers/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/audiences/researchers/page.tsx',
    description:
      'Registered surface /public/audiences/researchers. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/public/audiences/researchers/page.tsx.',
  },
  {
    id: 'public-public-channels',
    domain: 'public',
    path: '/public/channels',
    status: 'live',
    endpoint: '/api/v1/ussd/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/channels/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/channels/page.tsx',
    description:
      'Registered surface /public/channels. Gateway contract: GET /api/v1/ussd/status, registered in apps/web/src/app/[locale]/public/channels/page.tsx.',
  },
  {
    id: 'public-public-components-api-playground',
    domain: 'public',
    path: '/public/components/api-playground',
    status: 'live',
    endpoint: '/api/v1/tool-registry',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/api-playground/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/api-playground/page.tsx',
    description:
      'Registered surface /public/components/api-playground. Gateway contract: GET /api/v1/tool-registry, registered in apps/web/src/app/[locale]/public/components/api-playground/page.tsx.',
  },
  {
    id: 'public-public-components-dispute-resolution',
    domain: 'public',
    path: '/public/components/dispute-resolution',
    status: 'live',
    endpoint: '/api/v1/disputes/{dispute_id}',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/dispute-resolution/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/dispute-resolution/page.tsx',
    description:
      'Registered surface /public/components/dispute-resolution. Gateway contract: GET /api/v1/disputes/{dispute_id}, registered in apps/web/src/app/[locale]/public/components/dispute-resolution/page.tsx.',
  },
  {
    id: 'public-public-components-ecowallet',
    domain: 'public',
    path: '/public/components/ecowallet',
    status: 'live',
    endpoint: '/api/v1/ecowallet/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/ecowallet/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/ecowallet/page.tsx',
    description:
      'Registered surface /public/components/ecowallet. Gateway contract: GET /api/v1/ecowallet/health, registered in apps/web/src/app/[locale]/public/components/ecowallet/page.tsx.',
  },
  {
    id: 'public-public-components-hydroma-engine',
    domain: 'public',
    path: '/public/components/hydroma-engine',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/hydroma-engine/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/hydroma-engine/page.tsx',
    description:
      'Registered surface /public/components/hydroma-engine. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/public/components/hydroma-engine/page.tsx.',
  },
  {
    id: 'public-public-components-land-profiler',
    domain: 'public',
    path: '/public/components/land-profiler',
    status: 'live',
    endpoint: '/api/v1/land/profiles',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/land-profiler/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/land-profiler/page.tsx',
    description:
      'Registered surface /public/components/land-profiler. Gateway contract: GET /api/v1/land/profiles, registered in apps/web/src/app/[locale]/public/components/land-profiler/page.tsx.',
  },
  {
    id: 'public-public-components-marketplace',
    domain: 'public',
    path: '/public/components/marketplace',
    status: 'live',
    endpoint: '/api/v1/marketplace/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/marketplace/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/marketplace/page.tsx',
    description:
      'Registered surface /public/components/marketplace. Gateway contract: GET /api/v1/marketplace/stats, registered in apps/web/src/app/[locale]/public/components/marketplace/page.tsx.',
  },
  {
    id: 'public-public-components-mrv-dashboard',
    domain: 'public',
    path: '/public/components/mrv-dashboard',
    status: 'live',
    endpoint: '/api/v1/mrv/public/dashboard-summary',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/mrv-dashboard/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/mrv-dashboard/page.tsx',
    description:
      'Registered surface /public/components/mrv-dashboard. Gateway contract: GET /api/v1/mrv/public/dashboard-summary, registered in apps/web/src/app/[locale]/public/components/mrv-dashboard/page.tsx.',
  },
  {
    id: 'public-public-components-satellite-view',
    domain: 'public',
    path: '/public/components/satellite-view',
    status: 'live',
    endpoint: '/api/v1/satellite/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/components/satellite-view/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/components/satellite-view/page.tsx',
    description:
      'Registered surface /public/components/satellite-view. Gateway contract: GET /api/v1/satellite/health, registered in apps/web/src/app/[locale]/public/components/satellite-view/page.tsx.',
  },
  {
    id: 'public-public-cta',
    domain: 'public',
    path: '/public/cta',
    status: 'live',
    endpoint: '/api/v1/newsletter/subscribe',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/cta/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/cta/page.tsx',
    description:
      'Registered surface /public/cta. Gateway contract: GET /api/v1/newsletter/subscribe, registered in apps/web/src/app/[locale]/public/cta/page.tsx.',
  },
  {
    id: 'public-public-goals-impact',
    domain: 'public',
    path: '/public/goals/impact',
    status: 'live',
    endpoint: '/api/v1/pilot/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/impact/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/impact/page.tsx',
    description:
      'Registered surface /public/goals/impact. Gateway contract: GET /api/v1/pilot/stats, registered in apps/web/src/app/[locale]/public/goals/impact/page.tsx.',
  },
  {
    id: 'public-public-goals-manifesto',
    domain: 'public',
    path: '/public/goals/manifesto',
    status: 'live',
    endpoint: '/api/v1/tool-registry/phases',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/manifesto/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/manifesto/page.tsx',
    description:
      'Registered surface /public/goals/manifesto. Gateway contract: GET /api/v1/tool-registry/phases, registered in apps/web/src/app/[locale]/public/goals/manifesto/page.tsx.',
  },
  {
    id: 'public-public-goals-mission',
    domain: 'public',
    path: '/public/goals/mission',
    status: 'live',
    endpoint: '/api/v1/blockchain/info',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/mission/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/mission/page.tsx',
    description:
      'Registered surface /public/goals/mission. Gateway contract: GET /api/v1/blockchain/info, registered in apps/web/src/app/[locale]/public/goals/mission/page.tsx.',
  },
  {
    id: 'public-public-goals-roadmap',
    domain: 'public',
    path: '/public/goals/roadmap',
    status: 'live',
    endpoint: '/api/v1/blockchain/phasegate/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/roadmap/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/roadmap/page.tsx',
    description:
      'Registered surface /public/goals/roadmap. Gateway contract: GET /api/v1/blockchain/phasegate/status, registered in apps/web/src/app/[locale]/public/goals/roadmap/page.tsx.',
  },
  {
    id: 'public-public-goals-values',
    domain: 'public',
    path: '/public/goals/values',
    status: 'live',
    endpoint: '/api/v1/ussd/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/values/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/values/page.tsx',
    description:
      'Registered surface /public/goals/values. Gateway contract: GET /api/v1/ussd/status, registered in apps/web/src/app/[locale]/public/goals/values/page.tsx.',
  },
  {
    id: 'public-public-goals-vision',
    domain: 'public',
    path: '/public/goals/vision',
    status: 'live',
    endpoint: '/api/v1/tool-registry',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/goals/vision/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/goals/vision/page.tsx',
    description:
      'Registered surface /public/goals/vision. Gateway contract: GET /api/v1/tool-registry, registered in apps/web/src/app/[locale]/public/goals/vision/page.tsx.',
  },
  {
    id: 'public-public-home',
    domain: 'public',
    path: '/public/home',
    status: 'live',
    endpoint: '/api/v1/platform/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/home/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/home/page.tsx',
    description:
      'Registered surface /public/home. Gateway contract: GET /api/v1/platform/stats, registered in apps/web/src/app/[locale]/public/home/page.tsx.',
  },
  {
    id: 'public-public-model-count',
    domain: 'public',
    path: '/public/model-count',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/model-count/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/model-count/page.tsx',
    description:
      'Registered surface /public/model-count. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/public/model-count/page.tsx.',
  },
  {
    id: 'public-public-pilot-apply',
    domain: 'public',
    path: '/public/pilot/apply',
    status: 'planned',
    endpoint: '/api/v1/pilot/apply',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/pilot.py',
    routeFile: null,
    description:
      'Registered surface /public/pilot/apply. Gateway contract: POST /api/v1/pilot/apply, registered in services/api_gateway/routers/pilot.py.',
  },
  {
    id: 'public-public-pilot-stats',
    domain: 'public',
    path: '/public/pilot/stats',
    status: 'planned',
    endpoint: '/api/v1/pilot/stats',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/pilot.py',
    routeFile: null,
    description:
      'Registered surface /public/pilot/stats. Gateway contract: GET /api/v1/pilot/stats, registered in services/api_gateway/routers/pilot.py.',
  },
  {
    id: 'public-public-policy-accessibility',
    domain: 'public',
    path: '/public/policy/accessibility',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/accessibility/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/accessibility/page.tsx',
    description:
      'Registered surface /public/policy/accessibility. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/accessibility/page.tsx.',
  },
  {
    id: 'public-public-policy-cookies',
    domain: 'public',
    path: '/public/policy/cookies',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/cookies/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/cookies/page.tsx',
    description:
      'Registered surface /public/policy/cookies. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/cookies/page.tsx.',
  },
  {
    id: 'public-public-policy-governance',
    domain: 'public',
    path: '/public/policy/governance',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/governance/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/governance/page.tsx',
    description:
      'Registered surface /public/policy/governance. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/governance/page.tsx.',
  },
  {
    id: 'public-public-policy-licensing',
    domain: 'public',
    path: '/public/policy/licensing',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/licensing/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/licensing/page.tsx',
    description:
      'Registered surface /public/policy/licensing. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/licensing/page.tsx.',
  },
  {
    id: 'public-public-policy-privacy',
    domain: 'public',
    path: '/public/policy/privacy',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/privacy/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/privacy/page.tsx',
    description:
      'Registered surface /public/policy/privacy. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/privacy/page.tsx.',
  },
  {
    id: 'public-public-policy-terms',
    domain: 'public',
    path: '/public/policy/terms',
    status: 'live',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/policy/terms/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/policy/terms/page.tsx',
    description:
      'Registered surface /public/policy/terms. Gateway contract: GET /api/v1/legal-texts/slugs, registered in apps/web/src/app/[locale]/public/policy/terms/page.tsx.',
  },
  {
    id: 'public-public-science-benchmarks',
    domain: 'public',
    path: '/public/science/benchmarks',
    status: 'live',
    endpoint: '/api/v1/hydroma/validation',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/benchmarks/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/benchmarks/page.tsx',
    description:
      'Registered surface /public/science/benchmarks. Gateway contract: GET /api/v1/hydroma/validation, registered in apps/web/src/app/[locale]/public/science/benchmarks/page.tsx.',
  },
  {
    id: 'public-public-science-case-studies',
    domain: 'public',
    path: '/public/science/case-studies',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/case-studies/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/case-studies/page.tsx',
    description:
      'Registered surface /public/science/case-studies. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/public/science/case-studies/page.tsx.',
  },
  {
    id: 'public-public-science-data-sources',
    domain: 'public',
    path: '/public/science/data-sources',
    status: 'live',
    endpoint: '/api/v1/science/datasets',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/data-sources/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/data-sources/page.tsx',
    description:
      'Registered surface /public/science/data-sources. Gateway contract: GET /api/v1/science/datasets, registered in apps/web/src/app/[locale]/public/science/data-sources/page.tsx.',
  },
  {
    id: 'public-public-science-evidence-base',
    domain: 'public',
    path: '/public/science/evidence-base',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/evidence-base/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/evidence-base/page.tsx',
    description:
      'Registered surface /public/science/evidence-base. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/public/science/evidence-base/page.tsx.',
  },
  {
    id: 'public-public-science-gap-analysis',
    domain: 'public',
    path: '/public/science/gap-analysis',
    status: 'live',
    endpoint: '/api/v1/science/model-cards',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/gap-analysis/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/gap-analysis/page.tsx',
    description:
      'Registered surface /public/science/gap-analysis. Gateway contract: GET /api/v1/science/model-cards, registered in apps/web/src/app/[locale]/public/science/gap-analysis/page.tsx.',
  },
  {
    id: 'public-public-science-limitations',
    domain: 'public',
    path: '/public/science/limitations',
    status: 'live',
    endpoint: '/api/v1/science/model-cards',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/limitations/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/limitations/page.tsx',
    description:
      'Registered surface /public/science/limitations. Gateway contract: GET /api/v1/science/model-cards, registered in apps/web/src/app/[locale]/public/science/limitations/page.tsx.',
  },
  {
    id: 'public-public-science-methodology',
    domain: 'public',
    path: '/public/science/methodology',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/methodology/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/methodology/page.tsx',
    description:
      'Registered surface /public/science/methodology. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/public/science/methodology/page.tsx.',
  },
  {
    id: 'public-public-science-peer-review',
    domain: 'public',
    path: '/public/science/peer-review',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/peer-review/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/peer-review/page.tsx',
    description:
      'Registered surface /public/science/peer-review. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/public/science/peer-review/page.tsx.',
  },
  {
    id: 'public-public-science-reproducibility',
    domain: 'public',
    path: '/public/science/reproducibility',
    status: 'live',
    endpoint: '/api/v1/hub/shared',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/reproducibility/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/reproducibility/page.tsx',
    description:
      'Registered surface /public/science/reproducibility. Gateway contract: GET /api/v1/hub/shared, registered in apps/web/src/app/[locale]/public/science/reproducibility/page.tsx.',
  },
  {
    id: 'public-public-science-uncertainty',
    domain: 'public',
    path: '/public/science/uncertainty',
    status: 'live',
    endpoint: '/api/v1/science/model-cards',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/uncertainty/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/uncertainty/page.tsx',
    description:
      'Registered surface /public/science/uncertainty. Gateway contract: GET /api/v1/science/model-cards, registered in apps/web/src/app/[locale]/public/science/uncertainty/page.tsx.',
  },
  {
    id: 'public-public-science-validation',
    domain: 'public',
    path: '/public/science/validation',
    status: 'live',
    endpoint: '/api/v1/hydroma/validation',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/validation/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/validation/page.tsx',
    description:
      'Registered surface /public/science/validation. Gateway contract: GET /api/v1/hydroma/validation, registered in apps/web/src/app/[locale]/public/science/validation/page.tsx.',
  },
  {
    id: 'public-public-science-validation-methods',
    domain: 'public',
    path: '/public/science/validation-methods',
    status: 'live',
    endpoint: '/api/v1/hydroma/validation',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/science/validation-methods/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/science/validation-methods/page.tsx',
    description:
      'Registered surface /public/science/validation-methods. Gateway contract: GET /api/v1/hydroma/validation, registered in apps/web/src/app/[locale]/public/science/validation-methods/page.tsx.',
  },
  {
    id: 'public-public-services-ai-advisor',
    domain: 'public',
    path: '/public/services/ai-advisor',
    status: 'live',
    endpoint: '/api/v1/ai/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/ai-advisor/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/ai-advisor/page.tsx',
    description:
      'Registered surface /public/services/ai-advisor. Gateway contract: GET /api/v1/ai/health, registered in apps/web/src/app/[locale]/public/services/ai-advisor/page.tsx.',
  },
  {
    id: 'public-public-services-api-access',
    domain: 'public',
    path: '/public/services/api-access',
    status: 'live',
    endpoint: '/api/v1/tool-registry',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/api-access/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/api-access/page.tsx',
    description:
      'Registered surface /public/services/api-access. Gateway contract: GET /api/v1/tool-registry, registered in apps/web/src/app/[locale]/public/services/api-access/page.tsx.',
  },
  {
    id: 'public-public-services-carbon-registry',
    domain: 'public',
    path: '/public/services/carbon-registry',
    status: 'live',
    endpoint: '/api/v1/hydroma/carbon',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/carbon-registry/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/carbon-registry/page.tsx',
    description:
      'Registered surface /public/services/carbon-registry. Gateway contract: GET /api/v1/hydroma/carbon, registered in apps/web/src/app/[locale]/public/services/carbon-registry/page.tsx.',
  },
  {
    id: 'public-public-services-land-intelligence',
    domain: 'public',
    path: '/public/services/land-intelligence',
    status: 'live',
    endpoint: '/api/v1/land/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/land-intelligence/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/land-intelligence/page.tsx',
    description:
      'Registered surface /public/services/land-intelligence. Gateway contract: GET /api/v1/land/health, registered in apps/web/src/app/[locale]/public/services/land-intelligence/page.tsx.',
  },
  {
    id: 'public-public-services-marketplace-access',
    domain: 'public',
    path: '/public/services/marketplace-access',
    status: 'live',
    endpoint: '/api/v1/marketplace/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/marketplace-access/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/marketplace-access/page.tsx',
    description:
      'Registered surface /public/services/marketplace-access. Gateway contract: GET /api/v1/marketplace/stats, registered in apps/web/src/app/[locale]/public/services/marketplace-access/page.tsx.',
  },
  {
    id: 'public-public-services-mrv-verification',
    domain: 'public',
    path: '/public/services/mrv-verification',
    status: 'live',
    endpoint: '/api/v1/mrv/public/dashboard-summary',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/mrv-verification/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/mrv-verification/page.tsx',
    description:
      'Registered surface /public/services/mrv-verification. Gateway contract: GET /api/v1/mrv/public/dashboard-summary, registered in apps/web/src/app/[locale]/public/services/mrv-verification/page.tsx.',
  },
  {
    id: 'public-public-services-offline-tools',
    domain: 'public',
    path: '/public/services/offline-tools',
    status: 'live',
    endpoint: '/api/v1/sync/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/offline-tools/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/offline-tools/page.tsx',
    description:
      'Registered surface /public/services/offline-tools. Gateway contract: GET /api/v1/sync/status, registered in apps/web/src/app/[locale]/public/services/offline-tools/page.tsx.',
  },
  {
    id: 'public-public-services-overview',
    domain: 'public',
    path: '/public/services/overview',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/overview/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/overview/page.tsx',
    description:
      'Registered surface /public/services/overview. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/public/services/overview/page.tsx.',
  },
  {
    id: 'public-public-services-satellite-intelligence',
    domain: 'public',
    path: '/public/services/satellite-intelligence',
    status: 'live',
    endpoint: '/api/v1/satellite/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/satellite-intelligence/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/satellite-intelligence/page.tsx',
    description:
      'Registered surface /public/services/satellite-intelligence. Gateway contract: GET /api/v1/satellite/health, registered in apps/web/src/app/[locale]/public/services/satellite-intelligence/page.tsx.',
  },
  {
    id: 'public-public-services-water-management',
    domain: 'public',
    path: '/public/services/water-management',
    status: 'live',
    endpoint: '/api/v1/hydroma/water',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/services/water-management/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/services/water-management/page.tsx',
    description:
      'Registered surface /public/services/water-management. Gateway contract: GET /api/v1/hydroma/water, registered in apps/web/src/app/[locale]/public/services/water-management/page.tsx.',
  },
  {
    id: 'public-public-visit',
    domain: 'public',
    path: '/public/visit',
    status: 'live',
    endpoint: '/api/v1/contact',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/visit/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/visit/page.tsx',
    description:
      'Registered surface /public/visit. Gateway contract: GET /api/v1/contact, registered in apps/web/src/app/[locale]/public/visit/page.tsx.',
  },
  {
    id: 'public-public-visit-request-submit',
    domain: 'public',
    path: '/public/visit-request-submit',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/public.ts',
    routeFile: null,
    description:
      'Registered surface /public/visit-request-submit. No gateway contract is published for it; apps/web/src/lib/api/public.ts is the only source of truth.',
  },
  {
    id: 'public-public-why',
    domain: 'public',
    path: '/public/why',
    status: 'live',
    endpoint: '/api/v1/hydroma/validation',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/why/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/why/page.tsx',
    description:
      'Registered surface /public/why. Gateway contract: GET /api/v1/hydroma/validation, registered in apps/web/src/app/[locale]/public/why/page.tsx.',
  },
  {
    id: 'public-references',
    domain: 'public',
    path: '/references',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/references/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/references/page.tsx',
    description:
      'Registered surface /references. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/references/page.tsx.',
  },
  {
    id: 'public-scientific-models',
    domain: 'public',
    path: '/scientific-models',
    status: 'live',
    endpoint: '/api/v1/models',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/scientific-models/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/scientific-models/page.tsx',
    description:
      'Registered surface /scientific-models. Gateway contract: GET /api/v1/models, registered in apps/web/src/app/[locale]/scientific-models/page.tsx.',
  },
  {
    id: 'public-services',
    domain: 'public',
    path: '/services',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/services/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/services/page.tsx',
    description:
      'Registered surface /services. No gateway contract is published for it; apps/web/src/app/[locale]/services/page.tsx is the only source of truth.',
  },
  {
    id: 'public-statements',
    domain: 'public',
    path: '/statements',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/statements/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/statements/page.tsx',
    description:
      'Registered surface /statements. No gateway contract is published for it; apps/web/src/app/[locale]/statements/page.tsx is the only source of truth.',
  },
  {
    id: 'public-trust',
    domain: 'public',
    path: '/trust',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/page.tsx',
    description:
      'Registered surface /trust. No gateway contract is published for it; apps/web/src/app/[locale]/trust/page.tsx is the only source of truth.',
  },
  {
    id: 'public-trust-audits',
    domain: 'public',
    path: '/trust/audits',
    status: 'live',
    endpoint: '/api/v1/admin/security/audit',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/audits/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/audits/page.tsx',
    description:
      'Registered surface /trust/audits. Gateway contract: GET /api/v1/admin/security/audit, registered in apps/web/src/app/[locale]/trust/audits/page.tsx.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-distribute',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/distribute',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/distribute',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/distribute. Gateway contract: POST /api/v1/blockchain/ecocoin/distribute, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-earn',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/earn',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/earn',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/earn. Gateway contract: POST /api/v1/blockchain/ecocoin/earn, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-health',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/health',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/health',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/health. Gateway contract: GET /api/v1/blockchain/ecocoin/health, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-redeem',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/redeem',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/redeem',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/redeem. Gateway contract: POST /api/v1/blockchain/ecocoin/redeem, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-stats',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/stats',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/stats',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/stats. Gateway contract: GET /api/v1/blockchain/ecocoin/stats, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-transfer',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/transfer',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/transfer',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/transfer. Gateway contract: POST /api/v1/blockchain/ecocoin/transfer, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecocoin-wallet',
    domain: 'public',
    path: '/trust/blockchain/ecocoin/wallet/{user_id}',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecocoin/wallet/{user_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecocoin/wallet/{user_id}. Gateway contract: GET /api/v1/blockchain/ecocoin/wallet/{user_id}, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecosystem-fund-grant',
    domain: 'public',
    path: '/trust/blockchain/ecosystem-fund/grant',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecosystem-fund/grant',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecosystem-fund/grant. Gateway contract: POST /api/v1/blockchain/ecosystem-fund/grant, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecosystem-fund-grant-approve',
    domain: 'public',
    path: '/trust/blockchain/ecosystem-fund/grant/{grant_id}/approve',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecosystem-fund/grant/{grant_id}/approve',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecosystem-fund/grant/{grant_id}/approve. Gateway contract: POST /api/v1/blockchain/ecosystem-fund/grant/{grant_id}/approve, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-ecosystem-fund-grant-milestone',
    domain: 'public',
    path: '/trust/blockchain/ecosystem-fund/grant/{grant_id}/milestone',
    status: 'planned',
    endpoint: '/api/v1/blockchain/ecosystem-fund/grant/{grant_id}/milestone',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/ecosystem-fund/grant/{grant_id}/milestone. Gateway contract: POST /api/v1/blockchain/ecosystem-fund/grant/{grant_id}/milestone, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-health',
    domain: 'public',
    path: '/trust/blockchain/health',
    status: 'planned',
    endpoint: '/api/v1/blockchain/health',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/health. Gateway contract: GET /api/v1/blockchain/health, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-impact-certificate',
    domain: 'public',
    path: '/trust/blockchain/impact/certificate',
    status: 'planned',
    endpoint: '/api/v1/blockchain/impact/certificate',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/impact/certificate. Gateway contract: POST /api/v1/blockchain/impact/certificate, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-impact-certificate-2',
    domain: 'public',
    path: '/trust/blockchain/impact/certificate/{certificate_id}',
    status: 'planned',
    endpoint: '/api/v1/blockchain/impact/certificate/{certificate_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/impact/certificate/{certificate_id}. Gateway contract: GET /api/v1/blockchain/impact/certificate/{certificate_id}, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-info',
    domain: 'public',
    path: '/trust/blockchain/info',
    status: 'planned',
    endpoint: '/api/v1/blockchain/info',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/info. Gateway contract: GET /api/v1/blockchain/info, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-oracle-attestation',
    domain: 'public',
    path: '/trust/blockchain/oracle/attestation',
    status: 'planned',
    endpoint: '/api/v1/blockchain/oracle/attestation',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/oracle/attestation. Gateway contract: POST /api/v1/blockchain/oracle/attestation, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-oracle-challenge',
    domain: 'public',
    path: '/trust/blockchain/oracle/challenge/{activity_id}',
    status: 'planned',
    endpoint: '/api/v1/blockchain/oracle/challenge/{activity_id}',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/oracle/challenge/{activity_id}. Gateway contract: POST /api/v1/blockchain/oracle/challenge/{activity_id}, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-oracle-metrics',
    domain: 'public',
    path: '/trust/blockchain/oracle/metrics/{activity_id}',
    status: 'planned',
    endpoint: '/api/v1/blockchain/oracle/metrics/{activity_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/oracle/metrics/{activity_id}. Gateway contract: GET /api/v1/blockchain/oracle/metrics/{activity_id}, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-oracle-report',
    domain: 'public',
    path: '/trust/blockchain/oracle/report',
    status: 'planned',
    endpoint: '/api/v1/blockchain/oracle/report',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/oracle/report. Gateway contract: POST /api/v1/blockchain/oracle/report, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-phasegate-activate',
    domain: 'public',
    path: '/trust/blockchain/phasegate/activate/{phase}',
    status: 'planned',
    endpoint: '/api/v1/blockchain/phasegate/activate/{phase}',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/phasegate/activate/{phase}. Gateway contract: POST /api/v1/blockchain/phasegate/activate/{phase}, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-phasegate-status',
    domain: 'public',
    path: '/trust/blockchain/phasegate/status',
    status: 'planned',
    endpoint: '/api/v1/blockchain/phasegate/status',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/phasegate/status. Gateway contract: GET /api/v1/blockchain/phasegate/status, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-treasury-balance',
    domain: 'public',
    path: '/trust/blockchain/treasury/balance',
    status: 'planned',
    endpoint: '/api/v1/blockchain/treasury/balance',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/treasury/balance. Gateway contract: GET /api/v1/blockchain/treasury/balance, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-treasury-proposal',
    domain: 'public',
    path: '/trust/blockchain/treasury/proposal',
    status: 'planned',
    endpoint: '/api/v1/blockchain/treasury/proposal',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/treasury/proposal. Gateway contract: POST /api/v1/blockchain/treasury/proposal, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-blockchain-treasury-proposal-approve',
    domain: 'public',
    path: '/trust/blockchain/treasury/proposal/{proposal_id}/approve',
    status: 'planned',
    endpoint: '/api/v1/blockchain/treasury/proposal/{proposal_id}/approve',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/blockchain.py',
    routeFile: null,
    description:
      'Registered surface /trust/blockchain/treasury/proposal/{proposal_id}/approve. Gateway contract: POST /api/v1/blockchain/treasury/proposal/{proposal_id}/approve, registered in services/api_gateway/routers/blockchain.py.',
  },
  {
    id: 'public-trust-carbon-registry',
    domain: 'public',
    path: '/trust/carbon-registry',
    status: 'live',
    endpoint: '/api/v1/carbon/verra/standards',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/carbon-registry/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/carbon-registry/page.tsx',
    description:
      'Registered surface /trust/carbon-registry. Gateway contract: GET /api/v1/carbon/verra/standards, registered in apps/web/src/app/[locale]/trust/carbon-registry/page.tsx.',
  },
  {
    id: 'public-trust-disclosure',
    domain: 'public',
    path: '/trust/disclosure',
    status: 'live',
    endpoint: '/api/v1/contact',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/disclosure/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/disclosure/page.tsx',
    description:
      'Registered surface /trust/disclosure. Gateway contract: GET /api/v1/contact, registered in apps/web/src/app/[locale]/trust/disclosure/page.tsx.',
  },
  {
    id: 'public-trust-provenance',
    domain: 'public',
    path: '/trust/provenance',
    status: 'live',
    endpoint: '/api/v1/admin/security/audit',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/provenance/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/provenance/page.tsx',
    description:
      'Registered surface /trust/provenance. Gateway contract: GET /api/v1/admin/security/audit, registered in apps/web/src/app/[locale]/trust/provenance/page.tsx.',
  },
  {
    id: 'public-trust-report',
    domain: 'public',
    path: '/trust/report',
    status: 'live',
    endpoint: '/api/v1/pilot/stats',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/report/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/report/page.tsx',
    description:
      'Registered surface /trust/report. Gateway contract: GET /api/v1/pilot/stats, registered in apps/web/src/app/[locale]/trust/report/page.tsx.',
  },
  {
    id: 'public-trust-sanctions',
    domain: 'public',
    path: '/trust/sanctions',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/trust/sanctions/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/trust/sanctions/page.tsx',
    description:
      'Registered surface /trust/sanctions. No gateway contract is published for it; apps/web/src/app/[locale]/trust/sanctions/page.tsx is the only source of truth.',
  },
  {
    id: 'public-validation',
    domain: 'public',
    path: '/validation',
    status: 'live',
    endpoint: '/api/v1/hydroma/validation',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/validation/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/validation/page.tsx',
    description:
      'Registered surface /validation. Gateway contract: GET /api/v1/hydroma/validation, registered in apps/web/src/app/[locale]/validation/page.tsx.',
  },
  {
    id: 'marketplace-market',
    domain: 'marketplace',
    path: '/market',
    status: 'live',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/page.tsx',
    description:
      'Registered surface /market. Gateway contract: GET /api/v1/marketplace/products, registered in apps/web/src/app/[locale]/market/page.tsx.',
  },
  {
    id: 'marketplace-market-admin-orders',
    domain: 'marketplace',
    path: '/market/admin/orders',
    status: 'planned',
    endpoint: '/api/v1/marketplace/admin/orders',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/admin/orders. Gateway contract: GET /api/v1/marketplace/admin/orders, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-admin-products-approve',
    domain: 'marketplace',
    path: '/market/admin/products/{product_id}/approve',
    status: 'planned',
    endpoint: '/api/v1/marketplace/admin/products/{product_id}/approve',
    method: 'PATCH',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/admin/products/{product_id}/approve. Gateway contract: PATCH /api/v1/marketplace/admin/products/{product_id}/approve, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-admin-stats',
    domain: 'marketplace',
    path: '/market/admin/stats',
    status: 'planned',
    endpoint: '/api/v1/marketplace/admin/stats',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/admin/stats. Gateway contract: GET /api/v1/marketplace/admin/stats, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-admin-vendors-approve',
    domain: 'marketplace',
    path: '/market/admin/vendors/{vendor_id}/approve',
    status: 'planned',
    endpoint: '/api/v1/marketplace/admin/vendors/{vendor_id}/approve',
    method: 'PATCH',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/admin/vendors/{vendor_id}/approve. Gateway contract: PATCH /api/v1/marketplace/admin/vendors/{vendor_id}/approve, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-bazaar-analytics',
    domain: 'marketplace',
    path: '/market/bazaar-analytics',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /market/bazaar-analytics. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars',
    domain: 'marketplace',
    path: '/market/bazaars',
    status: 'live',
    endpoint: '/api/v1/marketplace/marketplaces',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/page.tsx',
    description:
      'Registered surface /market/bazaars. Gateway contract: GET /api/v1/marketplace/marketplaces, registered in apps/web/src/app/[locale]/market/bazaars/page.tsx.',
  },
  {
    id: 'marketplace-market-bazaars-create',
    domain: 'marketplace',
    path: '/market/bazaars/create',
    status: 'live',
    endpoint: '/api/v1/marketplace/marketplaces',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/create/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/create/page.tsx',
    description:
      'Registered surface /market/bazaars/create. Gateway contract: GET /api/v1/marketplace/marketplaces, registered in apps/web/src/app/[locale]/market/bazaars/create/page.tsx.',
  },
  {
    id: 'marketplace-market-bazaars-2',
    domain: 'marketplace',
    path: '/market/bazaars/{id}',
    status: 'capability',
    endpoint: '/api/v1/marketplace/marketplaces',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}. Gateway contract: GET /api/v1/marketplace/marketplaces, registered in apps/web/src/app/[locale]/market/bazaars/[id]/page.tsx.',
  },
  {
    id: 'marketplace-market-bazaars-analytics',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/analytics',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/analytics/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/analytics/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/analytics. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/analytics/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-disputes',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/disputes',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/disputes/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/disputes/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/disputes. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/disputes/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-finances',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/finances',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/finances/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/finances/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/finances. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/finances/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-governance',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/governance',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/governance/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/governance/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/governance. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/governance/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-map',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/map',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/map/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/map/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/map. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/map/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-settings',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/settings',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/settings/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/settings/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/settings. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/settings/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-stores',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/stores',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/stores/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/stores/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/stores. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/stores/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-supervision',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/supervision',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/supervision/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/supervision/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/supervision. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/supervision/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step1',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step1',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step1/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step1/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step1. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step1/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step10',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step10',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step10/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step10/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step10. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step10/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step2',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step2',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step2/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step2/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step2. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step2/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step3',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step3',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step3/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step3/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step3. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step3/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step4',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step4',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step4/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step4/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step4. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step4/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step5',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step5',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step5/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step5/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step5. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step5/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step6',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step6',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step6/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step6/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step6. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step6/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step7',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step7',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step7/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step7/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step7. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step7/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step8',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step8',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step8/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step8/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step8. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step8/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-bazaars-wizard-step9',
    domain: 'marketplace',
    path: '/market/bazaars/{id}/wizard/step9',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step9/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step9/page.tsx',
    description:
      'Registered surface /market/bazaars/{id}/wizard/step9. No gateway contract is published for it; apps/web/src/app/[locale]/market/bazaars/[id]/wizard/step9/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-cart',
    domain: 'marketplace',
    path: '/market/cart',
    status: 'live',
    endpoint: '/api/v1/marketplace/cart',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/cart/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/cart/page.tsx',
    description:
      'Registered surface /market/cart. Gateway contract: GET /api/v1/marketplace/cart, registered in apps/web/src/app/[locale]/market/cart/page.tsx.',
  },
  {
    id: 'marketplace-market-cart-2',
    domain: 'marketplace',
    path: '/market/cart/{product_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/cart/{product_id}',
    method: 'DELETE',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/cart/{product_id}. Gateway contract: DELETE /api/v1/marketplace/cart/{product_id}, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-categories',
    domain: 'marketplace',
    path: '/market/categories',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/categories/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/categories/page.tsx',
    description:
      'Registered surface /market/categories. No gateway contract is published for it; apps/web/src/app/[locale]/market/categories/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-categories-2',
    domain: 'marketplace',
    path: '/market/categories/{level1}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/categories/[level1]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/categories/[level1]/page.tsx',
    description:
      'Registered surface /market/categories/{level1}. No gateway contract is published for it; apps/web/src/app/[locale]/market/categories/[level1]/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-categories-3',
    domain: 'marketplace',
    path: '/market/categories/{level1}/{level2}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/categories/[level1]/[level2]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/categories/[level1]/[level2]/page.tsx',
    description:
      'Registered surface /market/categories/{level1}/{level2}. No gateway contract is published for it; apps/web/src/app/[locale]/market/categories/[level1]/[level2]/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-categories-4',
    domain: 'marketplace',
    path: '/market/categories/{level1}/{level2}/{level3}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth:
      'apps/web/src/app/[locale]/market/categories/[level1]/[level2]/[level3]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/categories/[level1]/[level2]/[level3]/page.tsx',
    description:
      'Registered surface /market/categories/{level1}/{level2}/{level3}. No gateway contract is published for it; apps/web/src/app/[locale]/market/categories/[level1]/[level2]/[level3]/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-checkout',
    domain: 'marketplace',
    path: '/market/checkout',
    status: 'live',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/page.tsx',
    description:
      'Registered surface /market/checkout. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/checkout/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-card',
    domain: 'marketplace',
    path: '/market/checkout/card',
    status: 'live',
    endpoint: '/api/v1/marketplace/payments',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/card/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/card/page.tsx',
    description:
      'Registered surface /market/checkout/card. Gateway contract: GET /api/v1/marketplace/payments, registered in apps/web/src/app/[locale]/market/checkout/card/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-cart-review',
    domain: 'marketplace',
    path: '/market/checkout/cart-review',
    status: 'live',
    endpoint: '/api/v1/marketplace/cart',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/cart-review/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/cart-review/page.tsx',
    description:
      'Registered surface /market/checkout/cart-review. Gateway contract: GET /api/v1/marketplace/cart, registered in apps/web/src/app/[locale]/market/checkout/cart-review/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-confirmation',
    domain: 'marketplace',
    path: '/market/checkout/confirmation',
    status: 'live',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/confirmation/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/confirmation/page.tsx',
    description:
      'Registered surface /market/checkout/confirmation. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/checkout/confirmation/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-contract',
    domain: 'marketplace',
    path: '/market/checkout/contract',
    status: 'live',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/contract/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/contract/page.tsx',
    description:
      'Registered surface /market/checkout/contract. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/checkout/contract/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-ecowallet',
    domain: 'marketplace',
    path: '/market/checkout/ecowallet',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/ecowallet/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/ecowallet/page.tsx',
    description:
      'Registered surface /market/checkout/ecowallet. No gateway contract is published for it; apps/web/src/app/[locale]/market/checkout/ecowallet/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-checkout-escrow-setup',
    domain: 'marketplace',
    path: '/market/checkout/escrow-setup',
    status: 'live',
    endpoint: '/api/v1/marketplace/payments',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/escrow-setup/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/escrow-setup/page.tsx',
    description:
      'Registered surface /market/checkout/escrow-setup. Gateway contract: GET /api/v1/marketplace/payments, registered in apps/web/src/app/[locale]/market/checkout/escrow-setup/page.tsx.',
  },
  {
    id: 'marketplace-market-checkout-transaction-key',
    domain: 'marketplace',
    path: '/market/checkout/transaction-key',
    status: 'live',
    endpoint: '/api/v1/marketplace/payments',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/checkout/transaction-key/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/checkout/transaction-key/page.tsx',
    description:
      'Registered surface /market/checkout/transaction-key. Gateway contract: GET /api/v1/marketplace/payments, registered in apps/web/src/app/[locale]/market/checkout/transaction-key/page.tsx.',
  },
  {
    id: 'marketplace-market-compare',
    domain: 'marketplace',
    path: '/market/compare',
    status: 'live',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/compare/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/compare/page.tsx',
    description:
      'Registered surface /market/compare. Gateway contract: GET /api/v1/marketplace/products, registered in apps/web/src/app/[locale]/market/compare/page.tsx.',
  },
  {
    id: 'marketplace-market-escrow-dispute-arbitration',
    domain: 'marketplace',
    path: '/market/escrow-dispute-arbitration',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /market/escrow-dispute-arbitration. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'marketplace-market-escrow',
    domain: 'marketplace',
    path: '/market/escrow/{id}',
    status: 'capability',
    endpoint: '/api/v1/marketplace/payments',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/escrow/[id]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/escrow/[id]/page.tsx',
    description:
      'Registered surface /market/escrow/{id}. Gateway contract: GET /api/v1/marketplace/payments, registered in apps/web/src/app/[locale]/market/escrow/[id]/page.tsx.',
  },
  {
    id: 'marketplace-market-marketplaces',
    domain: 'marketplace',
    path: '/market/marketplaces',
    status: 'planned',
    endpoint: '/api/v1/marketplace/marketplaces',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/marketplaces. Gateway contract: POST /api/v1/marketplace/marketplaces, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-marketplaces-2',
    domain: 'marketplace',
    path: '/market/marketplaces/{marketplace_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/marketplaces/{marketplace_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/marketplaces/{marketplace_id}. Gateway contract: GET /api/v1/marketplace/marketplaces/{marketplace_id}, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-marketplaces-approve',
    domain: 'marketplace',
    path: '/market/marketplaces/{marketplace_id}/approve',
    status: 'planned',
    endpoint: '/api/v1/marketplace/marketplaces/{marketplace_id}/approve',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/marketplaces/{marketplace_id}/approve. Gateway contract: POST /api/v1/marketplace/marketplaces/{marketplace_id}/approve, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-marketplaces-members',
    domain: 'marketplace',
    path: '/market/marketplaces/{marketplace_id}/members',
    status: 'planned',
    endpoint: '/api/v1/marketplace/marketplaces/{marketplace_id}/members',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/marketplaces/{marketplace_id}/members. Gateway contract: POST /api/v1/marketplace/marketplaces/{marketplace_id}/members, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-marketplaces-shops',
    domain: 'marketplace',
    path: '/market/marketplaces/{marketplace_id}/shops',
    status: 'planned',
    endpoint: '/api/v1/marketplace/marketplaces/{marketplace_id}/shops',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/marketplaces/{marketplace_id}/shops. Gateway contract: GET /api/v1/marketplace/marketplaces/{marketplace_id}/shops, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-order-invoice',
    domain: 'marketplace',
    path: '/market/order-invoice',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /market/order-invoice. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'marketplace-market-orders',
    domain: 'marketplace',
    path: '/market/orders',
    status: 'live',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/orders/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/orders/page.tsx',
    description:
      'Registered surface /market/orders. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/orders/page.tsx.',
  },
  {
    id: 'marketplace-market-orders-dispute',
    domain: 'marketplace',
    path: '/market/orders/{id}/dispute',
    status: 'capability',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/orders/[id]/dispute/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/orders/[id]/dispute/page.tsx',
    description:
      'Registered surface /market/orders/{id}/dispute. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/orders/[id]/dispute/page.tsx.',
  },
  {
    id: 'marketplace-market-orders-evidence',
    domain: 'marketplace',
    path: '/market/orders/{id}/evidence',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/orders/[id]/evidence/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/orders/[id]/evidence/page.tsx',
    description:
      'Registered surface /market/orders/{id}/evidence. No gateway contract is published for it; apps/web/src/app/[locale]/market/orders/[id]/evidence/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-orders-timeline',
    domain: 'marketplace',
    path: '/market/orders/{id}/timeline',
    status: 'capability',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/orders/[id]/timeline/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/orders/[id]/timeline/page.tsx',
    description:
      'Registered surface /market/orders/{id}/timeline. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/orders/[id]/timeline/page.tsx.',
  },
  {
    id: 'marketplace-market-orders-tracking',
    domain: 'marketplace',
    path: '/market/orders/{id}/tracking',
    status: 'capability',
    endpoint: '/api/v1/marketplace/orders',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/orders/[id]/tracking/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/orders/[id]/tracking/page.tsx',
    description:
      'Registered surface /market/orders/{id}/tracking. Gateway contract: GET /api/v1/marketplace/orders, registered in apps/web/src/app/[locale]/market/orders/[id]/tracking/page.tsx.',
  },
  {
    id: 'marketplace-market-orders-complete',
    domain: 'marketplace',
    path: '/market/orders/{order_id}/complete',
    status: 'planned',
    endpoint: '/api/v1/marketplace/orders/{order_id}/complete',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/orders/{order_id}/complete. Gateway contract: POST /api/v1/marketplace/orders/{order_id}/complete, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-orders-confirm',
    domain: 'marketplace',
    path: '/market/orders/{order_id}/confirm',
    status: 'planned',
    endpoint: '/api/v1/marketplace/orders/{order_id}/confirm',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/orders/{order_id}/confirm. Gateway contract: POST /api/v1/marketplace/orders/{order_id}/confirm, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-orders-dispute-2',
    domain: 'marketplace',
    path: '/market/orders/{order_id}/dispute',
    status: 'planned',
    endpoint: '/api/v1/marketplace/orders/{order_id}/dispute',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/orders/{order_id}/dispute. Gateway contract: POST /api/v1/marketplace/orders/{order_id}/dispute, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-orders-settle',
    domain: 'marketplace',
    path: '/market/orders/{order_id}/settle',
    status: 'planned',
    endpoint: '/api/v1/marketplace/orders/{order_id}/settle',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/orders/{order_id}/settle. Gateway contract: POST /api/v1/marketplace/orders/{order_id}/settle, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-orders-track',
    domain: 'marketplace',
    path: '/market/orders/{order_id}/track',
    status: 'planned',
    endpoint: '/api/v1/marketplace/orders/{order_id}/track',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/orders/{order_id}/track. Gateway contract: GET /api/v1/marketplace/orders/{order_id}/track, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-payments',
    domain: 'marketplace',
    path: '/market/payments',
    status: 'planned',
    endpoint: '/api/v1/marketplace/payments',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/payments. Gateway contract: POST /api/v1/marketplace/payments, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-payments-confirm',
    domain: 'marketplace',
    path: '/market/payments/{payment_id}/confirm',
    status: 'planned',
    endpoint: '/api/v1/marketplace/payments/{payment_id}/confirm',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/payments/{payment_id}/confirm. Gateway contract: POST /api/v1/marketplace/payments/{payment_id}/confirm, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-payments-escrow',
    domain: 'marketplace',
    path: '/market/payments/{payment_id}/escrow',
    status: 'planned',
    endpoint: '/api/v1/marketplace/payments/{payment_id}/escrow',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/payments/{payment_id}/escrow. Gateway contract: GET /api/v1/marketplace/payments/{payment_id}/escrow, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-payments-escrow-refund',
    domain: 'marketplace',
    path: '/market/payments/{payment_id}/escrow/refund',
    status: 'planned',
    endpoint: '/api/v1/marketplace/payments/{payment_id}/escrow/refund',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/payments/{payment_id}/escrow/refund. Gateway contract: POST /api/v1/marketplace/payments/{payment_id}/escrow/refund, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-payments-escrow-release',
    domain: 'marketplace',
    path: '/market/payments/{payment_id}/escrow/release',
    status: 'planned',
    endpoint: '/api/v1/marketplace/payments/{payment_id}/escrow/release',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/payments/{payment_id}/escrow/release. Gateway contract: POST /api/v1/marketplace/payments/{payment_id}/escrow/release, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-producers',
    domain: 'marketplace',
    path: '/market/producers',
    status: 'planned',
    endpoint: '/api/v1/marketplace/producers',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/producers. Gateway contract: GET /api/v1/marketplace/producers, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-product',
    domain: 'marketplace',
    path: '/market/product/{id}',
    status: 'capability',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/page.tsx',
    description:
      'Registered surface /market/product/{id}. Gateway contract: GET /api/v1/marketplace/products, registered in apps/web/src/app/[locale]/market/product/[id]/page.tsx.',
  },
  {
    id: 'marketplace-market-product-bulk',
    domain: 'marketplace',
    path: '/market/product/{id}/bulk',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/bulk/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/bulk/page.tsx',
    description:
      'Registered surface /market/product/{id}/bulk. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/bulk/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-certifications',
    domain: 'marketplace',
    path: '/market/product/{id}/certifications',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/certifications/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/certifications/page.tsx',
    description:
      'Registered surface /market/product/{id}/certifications. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/certifications/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-compare',
    domain: 'marketplace',
    path: '/market/product/{id}/compare',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/compare/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/compare/page.tsx',
    description:
      'Registered surface /market/product/{id}/compare. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/compare/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-eco-impact',
    domain: 'marketplace',
    path: '/market/product/{id}/eco-impact',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/eco-impact/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/eco-impact/page.tsx',
    description:
      'Registered surface /market/product/{id}/eco-impact. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/eco-impact/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-pricing-history',
    domain: 'marketplace',
    path: '/market/product/{id}/pricing-history',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/pricing-history/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/pricing-history/page.tsx',
    description:
      'Registered surface /market/product/{id}/pricing-history. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/pricing-history/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-qa',
    domain: 'marketplace',
    path: '/market/product/{id}/qa',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/qa/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/qa/page.tsx',
    description:
      'Registered surface /market/product/{id}/qa. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/qa/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-reviews',
    domain: 'marketplace',
    path: '/market/product/{id}/reviews',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/reviews/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/reviews/page.tsx',
    description:
      'Registered surface /market/product/{id}/reviews. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/reviews/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-shipping',
    domain: 'marketplace',
    path: '/market/product/{id}/shipping',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/shipping/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/shipping/page.tsx',
    description:
      'Registered surface /market/product/{id}/shipping. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/shipping/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-similar',
    domain: 'marketplace',
    path: '/market/product/{id}/similar',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/similar/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/similar/page.tsx',
    description:
      'Registered surface /market/product/{id}/similar. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/similar/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-specs',
    domain: 'marketplace',
    path: '/market/product/{id}/specs',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/specs/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/specs/page.tsx',
    description:
      'Registered surface /market/product/{id}/specs. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/specs/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-product-traceability',
    domain: 'marketplace',
    path: '/market/product/{id}/traceability',
    status: 'capability',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/traceability/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/traceability/page.tsx',
    description:
      'Registered surface /market/product/{id}/traceability. Gateway contract: GET /api/v1/marketplace/products, registered in apps/web/src/app/[locale]/market/product/[id]/traceability/page.tsx.',
  },
  {
    id: 'marketplace-market-product-warranty',
    domain: 'marketplace',
    path: '/market/product/{id}/warranty',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/product/[id]/warranty/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/product/[id]/warranty/page.tsx',
    description:
      'Registered surface /market/product/{id}/warranty. No gateway contract is published for it; apps/web/src/app/[locale]/market/product/[id]/warranty/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-products',
    domain: 'marketplace',
    path: '/market/products',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products. Gateway contract: GET /api/v1/marketplace/products, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-search',
    domain: 'marketplace',
    path: '/market/products/search',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/search',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/search. Gateway contract: GET /api/v1/marketplace/products/search, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-2',
    domain: 'marketplace',
    path: '/market/products/{product_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/{product_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/{product_id}. Gateway contract: GET /api/v1/marketplace/products/{product_id}, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-carbon-credits',
    domain: 'marketplace',
    path: '/market/products/{product_id}/carbon-credits',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/{product_id}/carbon-credits',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/{product_id}/carbon-credits. Gateway contract: GET /api/v1/marketplace/products/{product_id}/carbon-credits, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-images',
    domain: 'marketplace',
    path: '/market/products/{product_id}/images',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/{product_id}/images',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/{product_id}/images. Gateway contract: POST /api/v1/marketplace/products/{product_id}/images, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-tokenize',
    domain: 'marketplace',
    path: '/market/products/{product_id}/tokenize',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/{product_id}/tokenize',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/{product_id}/tokenize. Gateway contract: POST /api/v1/marketplace/products/{product_id}/tokenize, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-products-trace',
    domain: 'marketplace',
    path: '/market/products/{product_id}/trace',
    status: 'planned',
    endpoint: '/api/v1/marketplace/products/{product_id}/trace',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/products/{product_id}/trace. Gateway contract: GET /api/v1/marketplace/products/{product_id}/trace, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-search',
    domain: 'marketplace',
    path: '/market/search',
    status: 'live',
    endpoint: '/api/v1/marketplace/products/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/page.tsx',
    description:
      'Registered surface /market/search. Gateway contract: GET /api/v1/marketplace/products/search, registered in apps/web/src/app/[locale]/market/search/page.tsx.',
  },
  {
    id: 'marketplace-market-search-advanced',
    domain: 'marketplace',
    path: '/market/search/advanced',
    status: 'live',
    endpoint: '/api/v1/marketplace/products/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/advanced/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/advanced/page.tsx',
    description:
      'Registered surface /market/search/advanced. Gateway contract: GET /api/v1/marketplace/products/search, registered in apps/web/src/app/[locale]/market/search/advanced/page.tsx.',
  },
  {
    id: 'marketplace-market-search-autocomplete',
    domain: 'marketplace',
    path: '/market/search/autocomplete',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/autocomplete/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/autocomplete/page.tsx',
    description:
      'Registered surface /market/search/autocomplete. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/autocomplete/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-barcode',
    domain: 'marketplace',
    path: '/market/search/barcode',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/barcode/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/barcode/page.tsx',
    description:
      'Registered surface /market/search/barcode. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/barcode/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-filters',
    domain: 'marketplace',
    path: '/market/search/filters',
    status: 'live',
    endpoint: '/api/v1/marketplace/products',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/filters/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/filters/page.tsx',
    description:
      'Registered surface /market/search/filters. Gateway contract: GET /api/v1/marketplace/products, registered in apps/web/src/app/[locale]/market/search/filters/page.tsx.',
  },
  {
    id: 'marketplace-market-search-history',
    domain: 'marketplace',
    path: '/market/search/history',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/history/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/history/page.tsx',
    description:
      'Registered surface /market/search/history. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/history/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-image',
    domain: 'marketplace',
    path: '/market/search/image',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/image/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/image/page.tsx',
    description:
      'Registered surface /market/search/image. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/image/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-nfc',
    domain: 'marketplace',
    path: '/market/search/nfc',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/nfc/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/nfc/page.tsx',
    description:
      'Registered surface /market/search/nfc. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/nfc/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-semantic',
    domain: 'marketplace',
    path: '/market/search/semantic',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/semantic/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/semantic/page.tsx',
    description:
      'Registered surface /market/search/semantic. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/semantic/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-suggestions',
    domain: 'marketplace',
    path: '/market/search/suggestions',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/suggestions/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/suggestions/page.tsx',
    description:
      'Registered surface /market/search/suggestions. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/suggestions/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-visual',
    domain: 'marketplace',
    path: '/market/search/visual',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/visual/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/visual/page.tsx',
    description:
      'Registered surface /market/search/visual. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/visual/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-search-voice',
    domain: 'marketplace',
    path: '/market/search/voice',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/search/voice/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/search/voice/page.tsx',
    description:
      'Registered surface /market/search/voice. No gateway contract is published for it; apps/web/src/app/[locale]/market/search/voice/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-stats',
    domain: 'marketplace',
    path: '/market/stats',
    status: 'planned',
    endpoint: '/api/v1/marketplace/stats',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/stats. Gateway contract: GET /api/v1/marketplace/stats, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-stores-create',
    domain: 'marketplace',
    path: '/market/stores/create',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/stores/create/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/stores/create/page.tsx',
    description:
      'Registered surface /market/stores/create. No gateway contract is published for it; apps/web/src/app/[locale]/market/stores/create/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-stores-create-step1',
    domain: 'marketplace',
    path: '/market/stores/create/step1',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/stores/create/step1/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/stores/create/step1/page.tsx',
    description:
      'Registered surface /market/stores/create/step1. No gateway contract is published for it; apps/web/src/app/[locale]/market/stores/create/step1/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-stores-create-step2',
    domain: 'marketplace',
    path: '/market/stores/create/step2',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/stores/create/step2/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/stores/create/step2/page.tsx',
    description:
      'Registered surface /market/stores/create/step2. No gateway contract is published for it; apps/web/src/app/[locale]/market/stores/create/step2/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-stores',
    domain: 'marketplace',
    path: '/market/stores/{id}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/stores/[id]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/stores/[id]/page.tsx',
    description:
      'Registered surface /market/stores/{id}. No gateway contract is published for it; apps/web/src/app/[locale]/market/stores/[id]/page.tsx is the only source of truth.',
  },
  {
    id: 'marketplace-market-vendor-payouts',
    domain: 'marketplace',
    path: '/market/vendor-payouts',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /market/vendor-payouts. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'marketplace-market-vendors',
    domain: 'marketplace',
    path: '/market/vendors',
    status: 'planned',
    endpoint: '/api/v1/marketplace/vendors',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/vendors. Gateway contract: POST /api/v1/marketplace/vendors, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-vendors-2',
    domain: 'marketplace',
    path: '/market/vendors/{vendor_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/vendors/{vendor_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/vendors/{vendor_id}. Gateway contract: GET /api/v1/marketplace/vendors/{vendor_id}, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-vendors-orders',
    domain: 'marketplace',
    path: '/market/vendors/{vendor_id}/orders',
    status: 'planned',
    endpoint: '/api/v1/marketplace/vendors/{vendor_id}/orders',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/vendors/{vendor_id}/orders. Gateway contract: GET /api/v1/marketplace/vendors/{vendor_id}/orders, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-vendors-products',
    domain: 'marketplace',
    path: '/market/vendors/{vendor_id}/products',
    status: 'planned',
    endpoint: '/api/v1/marketplace/vendors/{vendor_id}/products',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/marketplace.py',
    routeFile: null,
    description:
      'Registered surface /market/vendors/{vendor_id}/products. Gateway contract: GET /api/v1/marketplace/vendors/{vendor_id}/products, registered in services/api_gateway/routers/marketplace.py.',
  },
  {
    id: 'marketplace-market-villages-b2b-demands',
    domain: 'marketplace',
    path: '/market/villages/b2b/demands',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/b2b/demands',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/b2b/demands. Gateway contract: POST /api/v1/marketplace/villages/b2b/demands, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-b2b-demands-my',
    domain: 'marketplace',
    path: '/market/villages/b2b/demands/my',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/b2b/demands/my',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/b2b/demands/my. Gateway contract: GET /api/v1/marketplace/villages/b2b/demands/my, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-b2b-matches',
    domain: 'marketplace',
    path: '/market/villages/b2b/matches/{village_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/b2b/matches/{village_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/b2b/matches/{village_id}. Gateway contract: GET /api/v1/marketplace/villages/b2b/matches/{village_id}, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-engagements',
    domain: 'marketplace',
    path: '/market/villages/engagements',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/engagements',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/engagements. Gateway contract: POST /api/v1/marketplace/villages/engagements, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-entrepreneurs',
    domain: 'marketplace',
    path: '/market/villages/entrepreneurs',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/entrepreneurs',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/entrepreneurs. Gateway contract: GET /api/v1/marketplace/villages/entrepreneurs, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-entrepreneurs-me',
    domain: 'marketplace',
    path: '/market/villages/entrepreneurs/me',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/entrepreneurs/me',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/entrepreneurs/me. Gateway contract: GET /api/v1/marketplace/villages/entrepreneurs/me, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-events-register',
    domain: 'marketplace',
    path: '/market/villages/events/{event_id}/register',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/events/{event_id}/register',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/events/{event_id}/register. Gateway contract: POST /api/v1/marketplace/villages/events/{event_id}/register, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-festivals',
    domain: 'marketplace',
    path: '/market/villages/festivals',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/festivals',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/festivals. Gateway contract: POST /api/v1/marketplace/villages/festivals, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-investments',
    domain: 'marketplace',
    path: '/market/villages/investments',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/investments',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/investments. Gateway contract: GET /api/v1/marketplace/villages/investments, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-nomadic-communities',
    domain: 'marketplace',
    path: '/market/villages/nomadic-communities',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/nomadic-communities',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/nomadic-communities. Gateway contract: GET /api/v1/marketplace/villages/nomadic-communities, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-opportunities',
    domain: 'marketplace',
    path: '/market/villages/opportunities',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/opportunities',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/opportunities. Gateway contract: GET /api/v1/marketplace/villages/opportunities, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-opportunities-interest',
    domain: 'marketplace',
    path: '/market/villages/opportunities/{opportunity_id}/interest',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/opportunities/{opportunity_id}/interest',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/opportunities/{opportunity_id}/interest. Gateway contract: POST /api/v1/marketplace/villages/opportunities/{opportunity_id}/interest, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-opportunities-team',
    domain: 'marketplace',
    path: '/market/villages/opportunities/{opportunity_id}/team',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/opportunities/{opportunity_id}/team',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/opportunities/{opportunity_id}/team. Gateway contract: GET /api/v1/marketplace/villages/opportunities/{opportunity_id}/team, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-projects-engaged',
    domain: 'marketplace',
    path: '/market/villages/projects/{project_id}/engaged',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/projects/{project_id}/engaged',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/projects/{project_id}/engaged. Gateway contract: GET /api/v1/marketplace/villages/projects/{project_id}/engaged, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages',
    domain: 'marketplace',
    path: '/market/villages/{village_id}',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/{village_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/{village_id}. Gateway contract: GET /api/v1/marketplace/villages/{village_id}, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-villages-ai-recommendations',
    domain: 'marketplace',
    path: '/market/villages/{village_id}/ai-recommendations',
    status: 'planned',
    endpoint: '/api/v1/marketplace/villages/{village_id}/ai-recommendations',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/village_hub.py',
    routeFile: null,
    description:
      'Registered surface /market/villages/{village_id}/ai-recommendations. Gateway contract: POST /api/v1/marketplace/villages/{village_id}/ai-recommendations, registered in services/api_gateway/routers/village_hub.py.',
  },
  {
    id: 'marketplace-market-wallet',
    domain: 'marketplace',
    path: '/market/wallet',
    status: 'live',
    endpoint: '/api/v1/ecowallet',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/wallet/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/wallet/page.tsx',
    description:
      'Registered surface /market/wallet. Gateway contract: GET /api/v1/ecowallet, registered in apps/web/src/app/[locale]/market/wallet/page.tsx.',
  },
  {
    id: 'marketplace-market-2',
    domain: 'marketplace',
    path: '/market/{*segments}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/market/[...segments]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/market/[...segments]/page.tsx',
    description:
      'Registered surface /market/{*segments}. No gateway contract is published for it; apps/web/src/app/[locale]/market/[...segments]/page.tsx is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma',
    domain: 'hydroma',
    path: '/hydroma',
    status: 'live',
    endpoint: '/api/v1/models/cpp-status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/hydroma/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/hydroma/page.tsx',
    description:
      'Registered surface /hydroma. Gateway contract: GET /api/v1/models/cpp-status, registered in apps/web/src/app/[locale]/hydroma/page.tsx.',
  },
  {
    id: 'hydroma-hydroma-analyses-crop-water-req',
    domain: 'hydroma',
    path: '/hydroma/analyses/crop-water-req',
    status: 'planned',
    endpoint: '/analyses/crop-water-req',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/crop-water-req. Gateway contract: POST /analyses/crop-water-req, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-analyses-groundwater',
    domain: 'hydroma',
    path: '/hydroma/analyses/groundwater',
    status: 'planned',
    endpoint: '/analyses/groundwater',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/groundwater. Gateway contract: POST /analyses/groundwater, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-analyses-irrigation-design',
    domain: 'hydroma',
    path: '/hydroma/analyses/irrigation-design',
    status: 'planned',
    endpoint: '/analyses/irrigation-design',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/irrigation-design. Gateway contract: POST /analyses/irrigation-design, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-analyses-runoff',
    domain: 'hydroma',
    path: '/hydroma/analyses/runoff',
    status: 'planned',
    endpoint: '/analyses/runoff',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/runoff. Gateway contract: POST /analyses/runoff, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-analyses-structure-design',
    domain: 'hydroma',
    path: '/hydroma/analyses/structure-design',
    status: 'planned',
    endpoint: '/analyses/structure-design',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/structure-design. Gateway contract: POST /analyses/structure-design, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-analyses-topography',
    domain: 'hydroma',
    path: '/hydroma/analyses/topography',
    status: 'planned',
    endpoint: '/analyses/topography',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/analyses.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/analyses/topography. Gateway contract: POST /analyses/topography, registered in services/api_gateway/routers/analyses.py.',
  },
  {
    id: 'hydroma-hydroma-carbon',
    domain: 'hydroma',
    path: '/hydroma/carbon',
    status: 'planned',
    endpoint: '/api/v1/hydroma/carbon',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon. Gateway contract: GET /api/v1/hydroma/carbon, registered in openapi.json.',
  },
  {
    id: 'hydroma-hydroma-carbon-credits-balance',
    domain: 'hydroma',
    path: '/hydroma/carbon/credits/balance',
    status: 'planned',
    endpoint: '/api/v1/carbon/credits/balance',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/credits/balance. Gateway contract: GET /api/v1/carbon/credits/balance, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-credits-retire',
    domain: 'hydroma',
    path: '/hydroma/carbon/credits/retire',
    status: 'planned',
    endpoint: '/api/v1/carbon/credits/retire',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/credits/retire. Gateway contract: POST /api/v1/carbon/credits/retire, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-credits-transfer',
    domain: 'hydroma',
    path: '/hydroma/carbon/credits/transfer',
    status: 'planned',
    endpoint: '/api/v1/carbon/credits/transfer',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/credits/transfer. Gateway contract: POST /api/v1/carbon/credits/transfer, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-credits-history',
    domain: 'hydroma',
    path: '/hydroma/carbon/credits/{token_id}/history',
    status: 'planned',
    endpoint: '/api/v1/carbon/credits/{token_id}/history',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/credits/{token_id}/history. Gateway contract: GET /api/v1/carbon/credits/{token_id}/history, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-credits-verify',
    domain: 'hydroma',
    path: '/hydroma/carbon/credits/{token_id}/verify',
    status: 'planned',
    endpoint: '/api/v1/carbon/credits/{token_id}/verify',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/credits/{token_id}/verify. Gateway contract: GET /api/v1/carbon/credits/{token_id}/verify, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-tokenize',
    domain: 'hydroma',
    path: '/hydroma/carbon/tokenize',
    status: 'planned',
    endpoint: '/api/v1/carbon/tokenize',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/tokenize. Gateway contract: POST /api/v1/carbon/tokenize, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-verra-search',
    domain: 'hydroma',
    path: '/hydroma/carbon/verra/search',
    status: 'planned',
    endpoint: '/api/v1/carbon/verra/search',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/verra/search. Gateway contract: POST /api/v1/carbon/verra/search, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-verra-standards',
    domain: 'hydroma',
    path: '/hydroma/carbon/verra/standards',
    status: 'planned',
    endpoint: '/api/v1/carbon/verra/standards',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/verra/standards. Gateway contract: GET /api/v1/carbon/verra/standards, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-verra-sync',
    domain: 'hydroma',
    path: '/hydroma/carbon/verra/sync',
    status: 'planned',
    endpoint: '/api/v1/carbon/verra/sync',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/verra/sync. Gateway contract: POST /api/v1/carbon/verra/sync, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-verra',
    domain: 'hydroma',
    path: '/hydroma/carbon/verra/{registry_id}',
    status: 'planned',
    endpoint: '/api/v1/carbon/verra/{registry_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/verra/{registry_id}. Gateway contract: GET /api/v1/carbon/verra/{registry_id}, registered in services/api_gateway/routers/carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-2',
    domain: 'hydroma',
    path: '/hydroma/carbon/{model_id}',
    status: 'planned',
    endpoint: '/api/v1/hydroma/carbon/{model_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/{model_id}. Gateway contract: GET /api/v1/hydroma/carbon/{model_id}, registered in services/api_gateway/routers/hydroma_carbon.py.',
  },
  {
    id: 'hydroma-hydroma-carbon-run',
    domain: 'hydroma',
    path: '/hydroma/carbon/{model_id}/run',
    status: 'planned',
    endpoint: '/api/v1/hydroma/carbon/{model_id}/run',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_carbon.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/carbon/{model_id}/run. Gateway contract: POST /api/v1/hydroma/carbon/{model_id}/run, registered in services/api_gateway/routers/hydroma_carbon.py.',
  },
  {
    id: 'hydroma-hydroma-climate',
    domain: 'hydroma',
    path: '/hydroma/climate',
    status: 'planned',
    endpoint: '/api/v1/hydroma/climate',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /hydroma/climate. Gateway contract: GET /api/v1/hydroma/climate, registered in openapi.json.',
  },
  {
    id: 'hydroma-hydroma-climate-2',
    domain: 'hydroma',
    path: '/hydroma/climate/{model_id}',
    status: 'planned',
    endpoint: '/api/v1/hydroma/climate/{model_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_climate.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/climate/{model_id}. Gateway contract: GET /api/v1/hydroma/climate/{model_id}, registered in services/api_gateway/routers/hydroma_climate.py.',
  },
  {
    id: 'hydroma-hydroma-climate-run',
    domain: 'hydroma',
    path: '/hydroma/climate/{model_id}/run',
    status: 'planned',
    endpoint: '/api/v1/hydroma/climate/{model_id}/run',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_climate.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/climate/{model_id}/run. Gateway contract: POST /api/v1/hydroma/climate/{model_id}/run, registered in services/api_gateway/routers/hydroma_climate.py.',
  },
  {
    id: 'hydroma-hydroma-db-stats',
    domain: 'hydroma',
    path: '/hydroma/db-stats',
    status: 'planned',
    endpoint: '/api/v1/hydroma/db-stats',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_ops.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/db-stats. Gateway contract: GET /api/v1/hydroma/db-stats, registered in services/api_gateway/routers/hydroma_ops.py.',
  },
  {
    id: 'hydroma-hydroma-economics',
    domain: 'hydroma',
    path: '/hydroma/economics',
    status: 'planned',
    endpoint: '/api/v1/hydroma/economics',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /hydroma/economics. Gateway contract: GET /api/v1/hydroma/economics, registered in openapi.json.',
  },
  {
    id: 'hydroma-hydroma-economics-2',
    domain: 'hydroma',
    path: '/hydroma/economics/{model_id}',
    status: 'planned',
    endpoint: '/api/v1/hydroma/economics/{model_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_economics.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/economics/{model_id}. Gateway contract: GET /api/v1/hydroma/economics/{model_id}, registered in services/api_gateway/routers/hydroma_economics.py.',
  },
  {
    id: 'hydroma-hydroma-economics-run',
    domain: 'hydroma',
    path: '/hydroma/economics/{model_id}/run',
    status: 'planned',
    endpoint: '/api/v1/hydroma/economics/{model_id}/run',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_economics.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/economics/{model_id}/run. Gateway contract: POST /api/v1/hydroma/economics/{model_id}/run, registered in services/api_gateway/routers/hydroma_economics.py.',
  },
  {
    id: 'hydroma-hydroma-elevation-erosion-effect',
    domain: 'hydroma',
    path: '/hydroma/elevation/erosion-effect/{site_id}',
    status: 'planned',
    endpoint: '/api/v1/elevation/erosion-effect/{site_id}',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/elevation.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/elevation/erosion-effect/{site_id}. Gateway contract: POST /api/v1/elevation/erosion-effect/{site_id}, registered in services/api_gateway/routers/elevation.py.',
  },
  {
    id: 'hydroma-hydroma-elevation-grid',
    domain: 'hydroma',
    path: '/hydroma/elevation/grid/{site_id}',
    status: 'planned',
    endpoint: '/api/v1/elevation/grid/{site_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/elevation.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/elevation/grid/{site_id}. Gateway contract: GET /api/v1/elevation/grid/{site_id}, registered in services/api_gateway/routers/elevation.py.',
  },
  {
    id: 'hydroma-hydroma-farms',
    domain: 'hydroma',
    path: '/hydroma/farms',
    status: 'planned',
    endpoint: '/api/v1/farms',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/farms.py',
    routeFile: null,
    description:
      'Registered surface /hydroma/farms. Gateway contract: GET /api/v1/farms, registered in services/api_gateway/routers/farms.py.',
  },
  {
    id: 'hydroma-hydroma-tools-aquacrop-runner',
    domain: 'hydroma',
    path: '/hydroma/tools/aquacrop-runner',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/simulation/runners/aquacrop_runner.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/aquacrop-runner. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/simulation/runners/aquacrop_runner.py.',
  },
  {
    id: 'hydroma-hydroma-tools-aquacrop-runner-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/aquacrop-runner/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/aquacrop-runner/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-carbon-calculator',
    domain: 'hydroma',
    path: '/hydroma/tools/carbon-calculator',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/carbon/calculator.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/carbon-calculator. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/carbon/calculator.py.',
  },
  {
    id: 'hydroma-hydroma-tools-carbon-calculator-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/carbon-calculator/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/carbon-calculator/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-climate-adaptive-phenology',
    domain: 'hydroma',
    path: '/hydroma/tools/climate-adaptive-phenology',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/climate_adaptive_phenology.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/climate-adaptive-phenology. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/climate_adaptive_phenology.py.',
  },
  {
    id: 'hydroma-hydroma-tools-climate-adaptive-phenology-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/climate-adaptive-phenology/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/climate-adaptive-phenology/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-crop-scenarios',
    domain: 'hydroma',
    path: '/hydroma/tools/crop-scenarios',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/scenarios/crop_scenarios.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/crop-scenarios. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/scenarios/crop_scenarios.py.',
  },
  {
    id: 'hydroma-hydroma-tools-crop-scenarios-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/crop-scenarios/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/crop-scenarios/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-crop-water-requirement',
    domain: 'hydroma',
    path: '/hydroma/tools/crop-water-requirement',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/calculations/crop_water_req_calc.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/crop-water-requirement. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/calculations/crop_water_req_calc.py.',
  },
  {
    id: 'hydroma-hydroma-tools-crop-water-requirement-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/crop-water-requirement/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/crop-water-requirement/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-decision-support',
    domain: 'hydroma',
    path: '/hydroma/tools/decision-support',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/decision_support/dss.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/decision-support. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/decision_support/dss.py.',
  },
  {
    id: 'hydroma-hydroma-tools-decision-support-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/decision-support/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/decision-support/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-dynamic-stress-engine',
    domain: 'hydroma',
    path: '/hydroma/tools/dynamic-stress-engine',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/dynamic_stress_engine.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/dynamic-stress-engine. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/dynamic_stress_engine.py.',
  },
  {
    id: 'hydroma-hydroma-tools-dynamic-stress-engine-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/dynamic-stress-engine/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/dynamic-stress-engine/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-et0-calculator',
    domain: 'hydroma',
    path: '/hydroma/tools/et0-calculator',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate/et_calculator.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/et0-calculator. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate/et_calculator.py.',
  },
  {
    id: 'hydroma-hydroma-tools-et0-calculator-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/et0-calculator/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/et0-calculator/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-gaussian-process-surrogate',
    domain: 'hydroma',
    path: '/hydroma/tools/gaussian-process-surrogate',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/hybrid_ml/gp_surrogate.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/gaussian-process-surrogate. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/hybrid_ml/gp_surrogate.py.',
  },
  {
    id: 'hydroma-hydroma-tools-gaussian-process-surrogate-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/gaussian-process-surrogate/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/gaussian-process-surrogate/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-groundwater-model',
    domain: 'hydroma',
    path: '/hydroma/tools/groundwater-model',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/groundwater/models.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/groundwater-model. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/groundwater/models.py.',
  },
  {
    id: 'hydroma-hydroma-tools-groundwater-model-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/groundwater-model/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/groundwater-model/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-groundwater-service',
    domain: 'hydroma',
    path: '/hydroma/tools/groundwater-service',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/groundwater/service.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/groundwater-service. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/groundwater/service.py.',
  },
  {
    id: 'hydroma-hydroma-tools-groundwater-service-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/groundwater-service/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/groundwater-service/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-hecras-simulation',
    domain: 'hydroma',
    path: '/hydroma/tools/hecras-simulation',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/simulation/hecras.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/hecras-simulation. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/simulation/hecras.py.',
  },
  {
    id: 'hydroma-hydroma-tools-hecras-simulation-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/hecras-simulation/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/hecras-simulation/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-hydrology-fallback',
    domain: 'hydroma',
    path: '/hydroma/tools/hydrology-fallback',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/hydrology_fallback.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/hydrology-fallback. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/hydrology_fallback.py.',
  },
  {
    id: 'hydroma-hydroma-tools-hydrology-fallback-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/hydrology-fallback/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/hydrology-fallback/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-hydrology-fast',
    domain: 'hydroma',
    path: '/hydroma/tools/hydrology-fast',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/hydrology_fast.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/hydrology-fast. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/hydrology_fast.py.',
  },
  {
    id: 'hydroma-hydroma-tools-hydrology-fast-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/hydrology-fast/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/hydrology-fast/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-hydroma-core',
    domain: 'hydroma',
    path: '/hydroma/tools/hydroma-core',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/core/core.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/hydroma-core. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/core/core.py.',
  },
  {
    id: 'hydroma-hydroma-tools-hydroma-core-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/hydroma-core/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/hydroma-core/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-indices-fallback',
    domain: 'hydroma',
    path: '/hydroma/tools/indices-fallback',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/indices_fallback.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/indices-fallback. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/indices_fallback.py.',
  },
  {
    id: 'hydroma-hydroma-tools-indices-fallback-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/indices-fallback/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/indices-fallback/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-indices-fast',
    domain: 'hydroma',
    path: '/hydroma/tools/indices-fast',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/indices_fast.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/indices-fast. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/indices_fast.py.',
  },
  {
    id: 'hydroma-hydroma-tools-indices-fast-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/indices-fast/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/indices-fast/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-irrigation-scheduler',
    domain: 'hydroma',
    path: '/hydroma/tools/irrigation-scheduler',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/irrigation/scheduler.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/irrigation-scheduler. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/irrigation/scheduler.py.',
  },
  {
    id: 'hydroma-hydroma-tools-irrigation-scheduler-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/irrigation-scheduler/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/irrigation-scheduler/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-modflow6',
    domain: 'hydroma',
    path: '/hydroma/tools/modflow6',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/models/expansion/modflow6.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/modflow6. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/models/expansion/modflow6.py.',
  },
  {
    id: 'hydroma-hydroma-tools-modflow6-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/modflow6/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/modflow6/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-monte-carlo-scenarios',
    domain: 'hydroma',
    path: '/hydroma/tools/monte-carlo-scenarios',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/scenarios/monte_carlo.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/monte-carlo-scenarios. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/scenarios/monte_carlo.py.',
  },
  {
    id: 'hydroma-hydroma-tools-monte-carlo-scenarios-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/monte-carlo-scenarios/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/monte-carlo-scenarios/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-iot-ingest',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-iot-ingest',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/mrv/iot_ingest.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/mrv-iot-ingest. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/mrv/iot_ingest.py.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-iot-ingest-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-iot-ingest/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/mrv-iot-ingest/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-metrics',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-metrics',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/mrv/metrics.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/mrv-metrics. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/mrv/metrics.py.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-metrics-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-metrics/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/mrv-metrics/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-nojin',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-nojin',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/mrv/nojin_mrv.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/mrv-nojin. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/mrv/nojin_mrv.py.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-nojin-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-nojin/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/mrv-nojin/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-quality-assurance',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-quality-assurance',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/mrv/qa.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/mrv-quality-assurance. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/mrv/qa.py.',
  },
  {
    id: 'hydroma-hydroma-tools-mrv-quality-assurance-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/mrv-quality-assurance/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/mrv-quality-assurance/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-multi-stress-engine',
    domain: 'hydroma',
    path: '/hydroma/tools/multi-stress-engine',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/multi_stress_engine.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/multi-stress-engine. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/multi_stress_engine.py.',
  },
  {
    id: 'hydroma-hydroma-tools-multi-stress-engine-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/multi-stress-engine/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/multi-stress-engine/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-ndvi-analysis',
    domain: 'hydroma',
    path: '/hydroma/tools/ndvi-analysis',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/crop/ndvi_analysis.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/ndvi-analysis. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/crop/ndvi_analysis.py.',
  },
  {
    id: 'hydroma-hydroma-tools-ndvi-analysis-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/ndvi-analysis/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/ndvi-analysis/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-optimization-optimizer',
    domain: 'hydroma',
    path: '/hydroma/tools/optimization-optimizer',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/optimization/optimizer.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/optimization-optimizer. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/optimization/optimizer.py.',
  },
  {
    id: 'hydroma-hydroma-tools-optimization-optimizer-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/optimization-optimizer/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/optimization-optimizer/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-physics-informed-network',
    domain: 'hydroma',
    path: '/hydroma/tools/physics-informed-network',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/hybrid_ml/pinn.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/physics-informed-network. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/hybrid_ml/pinn.py.',
  },
  {
    id: 'hydroma-hydroma-tools-physics-informed-network-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/physics-informed-network/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/physics-informed-network/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-rothc-runner',
    domain: 'hydroma',
    path: '/hydroma/tools/rothc-runner',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/simulation/runners/rothc_runner.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/rothc-runner. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/simulation/runners/rothc_runner.py.',
  },
  {
    id: 'hydroma-hydroma-tools-rothc-runner-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/rothc-runner/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/rothc-runner/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-scenario-manager',
    domain: 'hydroma',
    path: '/hydroma/tools/scenario-manager',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/scenarios/scenario_manager.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/scenario-manager. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/scenarios/scenario_manager.py.',
  },
  {
    id: 'hydroma-hydroma-tools-scenario-manager-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/scenario-manager/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/scenario-manager/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-seed-optimization',
    domain: 'hydroma',
    path: '/hydroma/tools/seed-optimization',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/seed_optimization_engine.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/seed-optimization. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/seed_optimization_engine.py.',
  },
  {
    id: 'hydroma-hydroma-tools-seed-optimization-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/seed-optimization/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/seed-optimization/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-chemistry',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-chemistry',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/chemistry.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-chemistry. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/chemistry.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-chemistry-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-chemistry/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-chemistry/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-degradation-model',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-degradation-model',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/soil_degradation_model.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-degradation-model. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/soil_degradation_model.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-degradation-model-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-degradation-model/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-degradation-model/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-health',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-health',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/health.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-health. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/health.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-health-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-health/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-health/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-pedotransfer',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-pedotransfer',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/pedotransfer.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-pedotransfer. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/pedotransfer.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-pedotransfer-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-pedotransfer/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-pedotransfer/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/physics.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-physics. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/physics.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics-fallback',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics-fallback',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/soil_physics_fallback.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-physics-fallback. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/soil_physics_fallback.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics-fallback-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics-fallback/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-physics-fallback/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics-fast',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics-fast',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/soil_physics_fast.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-physics-fast. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/cpp_bridge/soil_physics_fast.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics-fast-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics-fast/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-physics-fast/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-physics-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-physics/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-physics/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-recommendations',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-recommendations',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/recommendations.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-recommendations. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/recommendations.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-recommendations-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-recommendations/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-recommendations/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-salinity',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-salinity',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/salinity.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-salinity. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/salinity.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-salinity-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-salinity/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-salinity/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-taxonomy',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-taxonomy',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/taxonomy.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-taxonomy. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/taxonomy.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-taxonomy-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-taxonomy/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-taxonomy/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-texture',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-texture',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/texture.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-texture. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/texture.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-texture-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-texture/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-texture/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-water-retention',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-water-retention',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/soil/water_retention.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/soil-water-retention. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/soil/water_retention.py.',
  },
  {
    id: 'hydroma-hydroma-tools-soil-water-retention-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/soil-water-retention/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/soil-water-retention/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-swat-plus',
    domain: 'hydroma',
    path: '/hydroma/tools/swat-plus',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/models/expansion/swat_plus.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/swat-plus. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/models/expansion/swat_plus.py.',
  },
  {
    id: 'hydroma-hydroma-tools-swat-plus-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/swat-plus/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/swat-plus/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-swat-runner',
    domain: 'hydroma',
    path: '/hydroma/tools/swat-runner',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/simulation/runners/swat_runner.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/swat-runner. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/simulation/runners/swat_runner.py.',
  },
  {
    id: 'hydroma-hydroma-tools-swat-runner-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/swat-runner/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/swat-runner/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-topographic-calculations',
    domain: 'hydroma',
    path: '/hydroma/tools/topographic-calculations',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/utils/topographic_calcs.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/topographic-calculations. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/utils/topographic_calcs.py.',
  },
  {
    id: 'hydroma-hydroma-tools-topographic-calculations-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/topographic-calculations/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/topographic-calculations/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-uncertainty-knowledge',
    domain: 'hydroma',
    path: '/hydroma/tools/uncertainty-knowledge',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/uncertainty_knowledge_engine.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/uncertainty-knowledge. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/climate_adaptation/uncertainty_knowledge_engine.py.',
  },
  {
    id: 'hydroma-hydroma-tools-uncertainty-knowledge-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/uncertainty-knowledge/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/uncertainty-knowledge/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-water-quality',
    domain: 'hydroma',
    path: '/hydroma/tools/water-quality',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/water/quality.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/water-quality. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/water/quality.py.',
  },
  {
    id: 'hydroma-hydroma-tools-water-quality-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/water-quality/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/water-quality/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-watershed-calculator',
    domain: 'hydroma',
    path: '/hydroma/tools/watershed-calculator',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/watershed/calculator.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/watershed-calculator. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/watershed/calculator.py.',
  },
  {
    id: 'hydroma-hydroma-tools-watershed-calculator-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/watershed-calculator/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/watershed-calculator/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-weap-simulation',
    domain: 'hydroma',
    path: '/hydroma/tools/weap-simulation',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/simulation/weap.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/weap-simulation. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/simulation/weap.py.',
  },
  {
    id: 'hydroma-hydroma-tools-weap-simulation-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/weap-simulation/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/weap-simulation/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools-what-if-engine',
    domain: 'hydroma',
    path: '/hydroma/tools/what-if-engine',
    status: 'capability',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'engine/hydroma/scenarios/whatif_engine.py',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/what-if-engine. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in engine/hydroma/scenarios/whatif_engine.py.',
  },
  {
    id: 'hydroma-hydroma-tools-what-if-engine-execute',
    domain: 'hydroma',
    path: '/hydroma/tools/what-if-engine/execute',
    status: 'unavailable',
    endpoint: null,
    method: 'POST',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /hydroma/tools/what-if-engine/execute. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'hydroma-hydroma-tools',
    domain: 'hydroma',
    path: '/hydroma/tools/{toolId}',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx',
    description:
      'Registered surface /hydroma/tools/{toolId}. No gateway contract is published for it; apps/web/src/app/[locale]/hydroma/tools/[toolId]/page.tsx is the only source of truth.',
  },
  {
    id: 'admin-admin',
    domain: 'admin',
    path: '/admin',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/page.tsx',
    description:
      'Registered surface /admin. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/admin/page.tsx.',
  },
  {
    id: 'admin-admin-audit-trail',
    domain: 'admin',
    path: '/admin/audit-trail',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /admin/audit-trail. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'admin-admin-automation-runs',
    domain: 'admin',
    path: '/admin/automation-runs',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /admin/automation-runs. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'admin-admin-bots',
    domain: 'admin',
    path: '/admin/bots',
    status: 'planned',
    endpoint: '/api/v1/admin/bots',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/bots. Gateway contract: GET /api/v1/admin/bots, registered in openapi.json.',
  },
  {
    id: 'admin-admin-bots-restart',
    domain: 'admin',
    path: '/admin/bots/{key}/restart',
    status: 'planned',
    endpoint: '/api/v1/admin/bots/{key}/restart',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/bots/{key}/restart. Gateway contract: POST /api/v1/admin/bots/{key}/restart, registered in openapi.json.',
  },
  {
    id: 'admin-admin-bots-toggle',
    domain: 'admin',
    path: '/admin/bots/{key}/toggle',
    status: 'planned',
    endpoint: '/api/v1/admin/bots/{key}/toggle',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/bots/{key}/toggle. Gateway contract: POST /api/v1/admin/bots/{key}/toggle, registered in openapi.json.',
  },
  {
    id: 'admin-admin-channel-health',
    domain: 'admin',
    path: '/admin/channel-health',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /admin/channel-health. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'admin-admin-content',
    domain: 'admin',
    path: '/admin/content',
    status: 'live',
    endpoint: '/api/v1/admin/content',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/content/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/content/page.tsx',
    description:
      'Registered surface /admin/content. Gateway contract: GET /api/v1/admin/content, registered in apps/web/src/app/[locale]/admin/content/page.tsx.',
  },
  {
    id: 'admin-admin-content-generate-draft',
    domain: 'admin',
    path: '/admin/content/generate-draft',
    status: 'planned',
    endpoint: '/api/v1/admin/content/generate-draft',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/generate-draft. Gateway contract: POST /api/v1/admin/content/generate-draft, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-2',
    domain: 'admin',
    path: '/admin/content/{item_id}',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}',
    method: 'PUT',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}. Gateway contract: PUT /api/v1/admin/content/{item_id}, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-cancel-schedule',
    domain: 'admin',
    path: '/admin/content/{item_id}/cancel-schedule',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/cancel-schedule',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/cancel-schedule. Gateway contract: POST /api/v1/admin/content/{item_id}/cancel-schedule, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-publish',
    domain: 'admin',
    path: '/admin/content/{item_id}/publish',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/publish',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/publish. Gateway contract: POST /api/v1/admin/content/{item_id}/publish, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-schedule',
    domain: 'admin',
    path: '/admin/content/{item_id}/schedule',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/schedule',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/schedule. Gateway contract: POST /api/v1/admin/content/{item_id}/schedule, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-translate',
    domain: 'admin',
    path: '/admin/content/{item_id}/translate',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/translate',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/translate. Gateway contract: POST /api/v1/admin/content/{item_id}/translate, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-translations',
    domain: 'admin',
    path: '/admin/content/{item_id}/translations',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/translations',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/translations. Gateway contract: GET /api/v1/admin/content/{item_id}/translations, registered in openapi.json.',
  },
  {
    id: 'admin-admin-content-versions',
    domain: 'admin',
    path: '/admin/content/{item_id}/versions',
    status: 'planned',
    endpoint: '/api/v1/admin/content/{item_id}/versions',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/content/{item_id}/versions. Gateway contract: GET /api/v1/admin/content/{item_id}/versions, registered in openapi.json.',
  },
  {
    id: 'admin-admin-design-tokens',
    domain: 'admin',
    path: '/admin/design-tokens',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/design-tokens/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/design-tokens/page.tsx',
    description:
      'Registered surface /admin/design-tokens. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/admin/design-tokens/page.tsx.',
  },
  {
    id: 'admin-admin-errors',
    domain: 'admin',
    path: '/admin/errors',
    status: 'planned',
    endpoint: '/api/v1/admin/errors',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors. Gateway contract: GET /api/v1/admin/errors, registered in openapi.json.',
  },
  {
    id: 'admin-admin-errors-summary',
    domain: 'admin',
    path: '/admin/errors/summary',
    status: 'planned',
    endpoint: '/api/v1/admin/errors/summary',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors/summary. Gateway contract: GET /api/v1/admin/errors/summary, registered in openapi.json.',
  },
  {
    id: 'admin-admin-errors-2',
    domain: 'admin',
    path: '/admin/errors/{error_id}',
    status: 'planned',
    endpoint: '/api/v1/admin/errors/{error_id}',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors/{error_id}. Gateway contract: GET /api/v1/admin/errors/{error_id}, registered in openapi.json.',
  },
  {
    id: 'admin-admin-errors-ack',
    domain: 'admin',
    path: '/admin/errors/{error_id}/ack',
    status: 'planned',
    endpoint: '/api/v1/admin/errors/{error_id}/ack',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors/{error_id}/ack. Gateway contract: POST /api/v1/admin/errors/{error_id}/ack, registered in openapi.json.',
  },
  {
    id: 'admin-admin-errors-resolve',
    domain: 'admin',
    path: '/admin/errors/{error_id}/resolve',
    status: 'planned',
    endpoint: '/api/v1/admin/errors/{error_id}/resolve',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors/{error_id}/resolve. Gateway contract: POST /api/v1/admin/errors/{error_id}/resolve, registered in openapi.json.',
  },
  {
    id: 'admin-admin-errors-suppress',
    domain: 'admin',
    path: '/admin/errors/{error_id}/suppress',
    status: 'planned',
    endpoint: '/api/v1/admin/errors/{error_id}/suppress',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/errors/{error_id}/suppress. Gateway contract: POST /api/v1/admin/errors/{error_id}/suppress, registered in openapi.json.',
  },
  {
    id: 'admin-admin-feature-flags',
    domain: 'admin',
    path: '/admin/feature-flags',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/feature-flags/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/feature-flags/page.tsx',
    description:
      'Registered surface /admin/feature-flags. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/admin/feature-flags/page.tsx.',
  },
  {
    id: 'admin-admin-jobs',
    domain: 'admin',
    path: '/admin/jobs',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/jobs/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/jobs/page.tsx',
    description:
      'Registered surface /admin/jobs. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/admin/jobs/page.tsx.',
  },
  {
    id: 'admin-admin-localization-translations',
    domain: 'admin',
    path: '/admin/localization/translations',
    status: 'live',
    endpoint: '/api/v1/legal-texts/locales',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/localization/translations/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/localization/translations/page.tsx',
    description:
      'Registered surface /admin/localization/translations. Gateway contract: GET /api/v1/legal-texts/locales, registered in apps/web/src/app/[locale]/admin/localization/translations/page.tsx.',
  },
  {
    id: 'admin-admin-message-catalogue-sync',
    domain: 'admin',
    path: '/admin/message-catalogue-sync',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /admin/message-catalogue-sync. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'admin-admin-models',
    domain: 'admin',
    path: '/admin/models',
    status: 'planned',
    endpoint: '/api/v1/admin/models',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/models. Gateway contract: GET /api/v1/admin/models, registered in openapi.json.',
  },
  {
    id: 'admin-admin-models-2',
    domain: 'admin',
    path: '/admin/models/{name}',
    status: 'planned',
    endpoint: '/api/v1/admin/models/{name}',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/models/{name}. Gateway contract: GET /api/v1/admin/models/{name}, registered in openapi.json.',
  },
  {
    id: 'admin-admin-models-load',
    domain: 'admin',
    path: '/admin/models/{name}/load',
    status: 'planned',
    endpoint: '/api/v1/admin/models/{name}/load',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/models/{name}/load. Gateway contract: POST /api/v1/admin/models/{name}/load, registered in openapi.json.',
  },
  {
    id: 'admin-admin-models-pull',
    domain: 'admin',
    path: '/admin/models/{name}/pull',
    status: 'planned',
    endpoint: '/api/v1/admin/models/{name}/pull',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/models/{name}/pull. Gateway contract: POST /api/v1/admin/models/{name}/pull, registered in openapi.json.',
  },
  {
    id: 'admin-admin-models-stop',
    domain: 'admin',
    path: '/admin/models/{name}/stop',
    status: 'planned',
    endpoint: '/api/v1/admin/models/{name}/stop',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/models/{name}/stop. Gateway contract: POST /api/v1/admin/models/{name}/stop, registered in openapi.json.',
  },
  {
    id: 'admin-admin-overview',
    domain: 'admin',
    path: '/admin/overview',
    status: 'planned',
    endpoint: '/api/v1/admin/overview',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/overview. Gateway contract: GET /api/v1/admin/overview, registered in openapi.json.',
  },
  {
    id: 'admin-admin-overview-health',
    domain: 'admin',
    path: '/admin/overview/health',
    status: 'planned',
    endpoint: '/api/v1/admin/overview/health',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/overview/health. Gateway contract: GET /api/v1/admin/overview/health, registered in openapi.json.',
  },
  {
    id: 'admin-admin-overview-metrics',
    domain: 'admin',
    path: '/admin/overview/metrics',
    status: 'planned',
    endpoint: '/api/v1/admin/overview/metrics',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/overview/metrics. Gateway contract: GET /api/v1/admin/overview/metrics, registered in openapi.json.',
  },
  {
    id: 'admin-admin-security',
    domain: 'admin',
    path: '/admin/security',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/security/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/security/page.tsx',
    description:
      'Registered surface /admin/security. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/admin/security/page.tsx.',
  },
  {
    id: 'admin-admin-security-audit',
    domain: 'admin',
    path: '/admin/security/audit',
    status: 'planned',
    endpoint: '/api/v1/admin/security/audit',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/security/audit. Gateway contract: GET /api/v1/admin/security/audit, registered in openapi.json.',
  },
  {
    id: 'admin-admin-security-logins',
    domain: 'admin',
    path: '/admin/security/logins',
    status: 'planned',
    endpoint: '/api/v1/admin/security/logins',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/security/logins. Gateway contract: GET /api/v1/admin/security/logins, registered in openapi.json.',
  },
  {
    id: 'admin-admin-settings',
    domain: 'admin',
    path: '/admin/settings',
    status: 'planned',
    endpoint: '/api/v1/admin/settings',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /admin/settings. Gateway contract: GET /api/v1/admin/settings, registered in openapi.json.',
  },
  {
    id: 'admin-admin-users',
    domain: 'admin',
    path: '/admin/users',
    status: 'live',
    endpoint: '/api/v1/admin/users',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/admin/users/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/admin/users/page.tsx',
    description:
      'Registered surface /admin/users. Gateway contract: GET /api/v1/admin/users, registered in apps/web/src/app/[locale]/admin/users/page.tsx.',
  },
  {
    id: 'research-research',
    domain: 'research',
    path: '/research',
    status: 'live',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/research/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/research/page.tsx',
    description:
      'Registered surface /research. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/research/page.tsx.',
  },
  {
    id: 'research-research-experiments-experiment-approval',
    domain: 'research',
    path: '/research/experiments/experiment-approval',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/experiment-approval. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-experiments-experiment-citations',
    domain: 'research',
    path: '/research/experiments/experiment-citations',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/experiment-citations. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-experiments-experiment-dataset',
    domain: 'research',
    path: '/research/experiments/experiment-dataset',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/experiment-dataset. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-experiments-experiment-run',
    domain: 'research',
    path: '/research/experiments/experiment-run',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/experiment-run. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-experiments-lab-protocol',
    domain: 'research',
    path: '/research/experiments/lab-protocol',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/lab-protocol. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-experiments-review-queue',
    domain: 'research',
    path: '/research/experiments/review-queue',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /research/experiments/review-queue. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'research-research-hub-runs',
    domain: 'research',
    path: '/research/hub/runs',
    status: 'planned',
    endpoint: '/api/v1/hub/runs',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_hub.py',
    routeFile: null,
    description:
      'Registered surface /research/hub/runs. Gateway contract: POST /api/v1/hub/runs, registered in services/api_gateway/routers/hydroma_hub.py.',
  },
  {
    id: 'research-research-hub-runs-share',
    domain: 'research',
    path: '/research/hub/runs/{run_id}/share',
    status: 'planned',
    endpoint: '/api/v1/hub/runs/{run_id}/share',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_hub.py',
    routeFile: null,
    description:
      'Registered surface /research/hub/runs/{run_id}/share. Gateway contract: POST /api/v1/hub/runs/{run_id}/share, registered in services/api_gateway/routers/hydroma_hub.py.',
  },
  {
    id: 'research-research-hub-shared',
    domain: 'research',
    path: '/research/hub/shared',
    status: 'planned',
    endpoint: '/api/v1/hub/shared',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/hydroma_hub.py',
    routeFile: null,
    description:
      'Registered surface /research/hub/shared. Gateway contract: GET /api/v1/hub/shared, registered in services/api_gateway/routers/hydroma_hub.py.',
  },
  {
    id: 'research-research-science-agrovoc',
    domain: 'research',
    path: '/research/science/agrovoc',
    status: 'planned',
    endpoint: '/api/v1/science/agrovoc',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/agrovoc. Gateway contract: GET /api/v1/science/agrovoc, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-citations',
    domain: 'research',
    path: '/research/science/citations',
    status: 'planned',
    endpoint: '/api/v1/science/citations',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/citations. Gateway contract: GET /api/v1/science/citations, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-citations-index',
    domain: 'research',
    path: '/research/science/citations/index',
    status: 'planned',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/citations/index. Gateway contract: GET /api/v1/science/citations/index, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-datasets',
    domain: 'research',
    path: '/research/science/datasets',
    status: 'planned',
    endpoint: '/api/v1/science/datasets',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/datasets. Gateway contract: GET /api/v1/science/datasets, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-datasets-doi',
    domain: 'research',
    path: '/research/science/datasets/{slug}/doi',
    status: 'planned',
    endpoint: '/api/v1/science/datasets/{slug}/doi',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/datasets/{slug}/doi. Gateway contract: POST /api/v1/science/datasets/{slug}/doi, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-model-cards',
    domain: 'research',
    path: '/research/science/model-cards',
    status: 'planned',
    endpoint: '/api/v1/science/model-cards',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/model-cards. Gateway contract: GET /api/v1/science/model-cards, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-science-zenodo-status',
    domain: 'research',
    path: '/research/science/zenodo/status',
    status: 'planned',
    endpoint: '/api/v1/science/zenodo/status',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/science.py',
    routeFile: null,
    description:
      'Registered surface /research/science/zenodo/status. Gateway contract: GET /api/v1/science/zenodo/status, registered in services/api_gateway/routers/science.py.',
  },
  {
    id: 'research-research-workspace',
    domain: 'research',
    path: '/research/workspace/{experimentId}',
    status: 'capability',
    endpoint: '/api/v1/science/citations/index',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/research/workspace/[experimentId]/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/research/workspace/[experimentId]/page.tsx',
    description:
      'Registered surface /research/workspace/{experimentId}. Gateway contract: GET /api/v1/science/citations/index, registered in apps/web/src/app/[locale]/research/workspace/[experimentId]/page.tsx.',
  },
  {
    id: 'system-help',
    domain: 'system',
    path: '/help',
    status: 'live',
    endpoint: '/api/v1/support/personas',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/help/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/help/page.tsx',
    description:
      'Registered surface /help. Gateway contract: GET /api/v1/support/personas, registered in apps/web/src/app/[locale]/help/page.tsx.',
  },
  {
    id: 'system-status',
    domain: 'system',
    path: '/status',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/status/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/status/page.tsx',
    description:
      'Registered surface /status. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/status/page.tsx.',
  },
  {
    id: 'system-system',
    domain: 'system',
    path: '/system',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/system/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/system/page.tsx',
    description:
      'Registered surface /system. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/system/page.tsx.',
  },
  {
    id: 'system-system-analytics-activity-timeline',
    domain: 'system',
    path: '/system/analytics/activity-timeline',
    status: 'planned',
    endpoint: '/api/v1/analytics/activity-timeline',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/activity-timeline. Gateway contract: GET /api/v1/analytics/activity-timeline, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-carbon-summary',
    domain: 'system',
    path: '/system/analytics/carbon-summary',
    status: 'planned',
    endpoint: '/api/v1/analytics/carbon-summary',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/carbon-summary. Gateway contract: GET /api/v1/analytics/carbon-summary, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-ndvi-trends',
    domain: 'system',
    path: '/system/analytics/ndvi-trends',
    status: 'planned',
    endpoint: '/api/v1/analytics/ndvi-trends',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/ndvi-trends. Gateway contract: GET /api/v1/analytics/ndvi-trends, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-overview',
    domain: 'system',
    path: '/system/analytics/overview',
    status: 'planned',
    endpoint: '/api/v1/analytics/overview',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/overview. Gateway contract: GET /api/v1/analytics/overview, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-performance-metrics',
    domain: 'system',
    path: '/system/analytics/performance-metrics',
    status: 'planned',
    endpoint: '/api/v1/analytics/performance-metrics',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/performance-metrics. Gateway contract: GET /api/v1/analytics/performance-metrics, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-scenario-impact',
    domain: 'system',
    path: '/system/analytics/scenario-impact',
    status: 'planned',
    endpoint: '/api/v1/analytics/scenario-impact',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/scenario-impact. Gateway contract: GET /api/v1/analytics/scenario-impact, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-analytics-soil-trends',
    domain: 'system',
    path: '/system/analytics/soil-trends',
    status: 'planned',
    endpoint: '/api/v1/analytics/soil-trends',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/analytics.py',
    routeFile: null,
    description:
      'Registered surface /system/analytics/soil-trends. Gateway contract: GET /api/v1/analytics/soil-trends, registered in services/api_gateway/routers/analytics.py.',
  },
  {
    id: 'system-system-automation-agent-run',
    domain: 'system',
    path: '/system/automation/agent-run',
    status: 'planned',
    endpoint: '/api/v1/automation/agent-run',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/automation.py',
    routeFile: null,
    description:
      'Registered surface /system/automation/agent-run. Gateway contract: POST /api/v1/automation/agent-run, registered in services/api_gateway/routers/automation.py.',
  },
  {
    id: 'system-system-automation-health',
    domain: 'system',
    path: '/system/automation/health',
    status: 'planned',
    endpoint: '/api/v1/automation/health',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/automation.py',
    routeFile: null,
    description:
      'Registered surface /system/automation/health. Gateway contract: GET /api/v1/automation/health, registered in services/api_gateway/routers/automation.py.',
  },
  {
    id: 'system-system-dashboard-data',
    domain: 'system',
    path: '/system/dashboard/data',
    status: 'planned',
    endpoint: '/dashboard/data',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    description:
      'Registered surface /system/dashboard/data. Gateway contract: GET /dashboard/data, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-analytics',
    domain: 'system',
    path: '/system/dashboard/public/analytics',
    status: 'planned',
    endpoint: '/dashboard/public/analytics',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/analytics. Gateway contract: GET /dashboard/public/analytics, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-carbon',
    domain: 'system',
    path: '/system/dashboard/public/carbon',
    status: 'planned',
    endpoint: '/dashboard/public/carbon',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/carbon. Gateway contract: GET /dashboard/public/carbon, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-full',
    domain: 'system',
    path: '/system/dashboard/public/full',
    status: 'planned',
    endpoint: '/dashboard/public/full',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/full. Gateway contract: GET /dashboard/public/full, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-mrv',
    domain: 'system',
    path: '/system/dashboard/public/mrv',
    status: 'planned',
    endpoint: '/dashboard/public/mrv',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/mrv. Gateway contract: GET /dashboard/public/mrv, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-projects',
    domain: 'system',
    path: '/system/dashboard/public/projects',
    status: 'planned',
    endpoint: '/dashboard/public/projects',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/projects. Gateway contract: GET /dashboard/public/projects, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-satellite',
    domain: 'system',
    path: '/system/dashboard/public/satellite',
    status: 'planned',
    endpoint: '/dashboard/public/satellite',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/satellite. Gateway contract: GET /dashboard/public/satellite, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-simulations',
    domain: 'system',
    path: '/system/dashboard/public/simulations',
    status: 'planned',
    endpoint: '/dashboard/public/simulations',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/simulations. Gateway contract: GET /dashboard/public/simulations, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-soil',
    domain: 'system',
    path: '/system/dashboard/public/soil',
    status: 'planned',
    endpoint: '/dashboard/public/soil',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/soil. Gateway contract: GET /dashboard/public/soil, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-test',
    domain: 'system',
    path: '/system/dashboard/public/test',
    status: 'planned',
    endpoint: '/dashboard/public/test',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/test. Gateway contract: GET /dashboard/public/test, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-tourism',
    domain: 'system',
    path: '/system/dashboard/public/tourism',
    status: 'planned',
    endpoint: '/dashboard/public/tourism',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/tourism. Gateway contract: GET /dashboard/public/tourism, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-public-weather',
    domain: 'system',
    path: '/system/dashboard/public/weather',
    status: 'planned',
    endpoint: '/dashboard/public/weather',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    access: 'public',
    description:
      'Registered surface /system/dashboard/public/weather. Gateway contract: GET /dashboard/public/weather, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-recommendations',
    domain: 'system',
    path: '/system/dashboard/recommendations/{farm_id}',
    status: 'planned',
    endpoint: '/dashboard/recommendations/{farm_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    description:
      'Registered surface /system/dashboard/recommendations/{farm_id}. Gateway contract: GET /dashboard/recommendations/{farm_id}, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-dashboard-refresh-data',
    domain: 'system',
    path: '/system/dashboard/refresh-data',
    status: 'planned',
    endpoint: '/dashboard/refresh-data',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/dashboard.py',
    routeFile: null,
    description:
      'Registered surface /system/dashboard/refresh-data. Gateway contract: POST /dashboard/refresh-data, registered in services/api_gateway/routers/dashboard.py.',
  },
  {
    id: 'system-system-incident-timeline',
    domain: 'system',
    path: '/system/incident-timeline',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /system/incident-timeline. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'system-system-iot-devices',
    domain: 'system',
    path: '/system/iot/devices',
    status: 'planned',
    endpoint: '/api/v1/iot/devices',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/iot_devices.py',
    routeFile: null,
    description:
      'Registered surface /system/iot/devices. Gateway contract: GET /api/v1/iot/devices, registered in services/api_gateway/routers/iot_devices.py.',
  },
  {
    id: 'system-system-iot-devices-provision-qr',
    domain: 'system',
    path: '/system/iot/devices/provision-qr',
    status: 'planned',
    endpoint: '/api/v1/iot/devices/provision-qr',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/iot_devices.py',
    routeFile: null,
    description:
      'Registered surface /system/iot/devices/provision-qr. Gateway contract: POST /api/v1/iot/devices/provision-qr, registered in services/api_gateway/routers/iot_devices.py.',
  },
  {
    id: 'system-system-iot-devices-2',
    domain: 'system',
    path: '/system/iot/devices/{device_id}',
    status: 'planned',
    endpoint: '/api/v1/iot/devices/{device_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/iot_devices.py',
    routeFile: null,
    description:
      'Registered surface /system/iot/devices/{device_id}. Gateway contract: GET /api/v1/iot/devices/{device_id}, registered in services/api_gateway/routers/iot_devices.py.',
  },
  {
    id: 'system-system-iot-devices-readings',
    domain: 'system',
    path: '/system/iot/devices/{device_id}/readings',
    status: 'planned',
    endpoint: '/api/v1/iot/devices/{device_id}/readings',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/iot_devices.py',
    routeFile: null,
    description:
      'Registered surface /system/iot/devices/{device_id}/readings. Gateway contract: GET /api/v1/iot/devices/{device_id}/readings, registered in services/api_gateway/routers/iot_devices.py.',
  },
  {
    id: 'system-system-iot-devices-status',
    domain: 'system',
    path: '/system/iot/devices/{device_id}/status',
    status: 'planned',
    endpoint: '/api/v1/iot/devices/{device_id}/status',
    method: 'PUT',
    sourceOfTruth: 'services/api_gateway/routers/iot_devices.py',
    routeFile: null,
    description:
      'Registered surface /system/iot/devices/{device_id}/status. Gateway contract: PUT /api/v1/iot/devices/{device_id}/status, registered in services/api_gateway/routers/iot_devices.py.',
  },
  {
    id: 'system-system-locale-fallback',
    domain: 'system',
    path: '/system/locale-fallback',
    status: 'live',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/system/locale-fallback/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/system/locale-fallback/page.tsx',
    description:
      'Registered surface /system/locale-fallback. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in apps/web/src/app/[locale]/system/locale-fallback/page.tsx.',
  },
  {
    id: 'system-system-migration-runner',
    domain: 'system',
    path: '/system/migration-runner',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /system/migration-runner. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'system-system-pwa-update',
    domain: 'system',
    path: '/system/pwa-update',
    status: 'live',
    endpoint: '/api/v1/tool-registry/{tool_id}',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/system/pwa-update/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/system/pwa-update/page.tsx',
    description:
      'Registered surface /system/pwa-update. Gateway contract: GET /api/v1/tool-registry/{tool_id}, registered in apps/web/src/app/[locale]/system/pwa-update/page.tsx.',
  },
  {
    id: 'system-system-queue-inspector',
    domain: 'system',
    path: '/system/queue-inspector',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /system/queue-inspector. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'system-system-webgpu-fallback',
    domain: 'system',
    path: '/system/webgpu-fallback',
    status: 'live',
    endpoint: '/api/v1/models/cpp-status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/system/webgpu-fallback/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/system/webgpu-fallback/page.tsx',
    description:
      'Registered surface /system/webgpu-fallback. Gateway contract: GET /api/v1/models/cpp-status, registered in apps/web/src/app/[locale]/system/webgpu-fallback/page.tsx.',
  },
  {
    id: 'workspace-workspace',
    domain: 'workspace',
    path: '/workspace',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/page.tsx',
    description:
      'Registered surface /workspace. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/page.tsx.',
  },
  {
    id: 'workspace-workspace-approvals',
    domain: 'workspace',
    path: '/workspace/approvals',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/approvals/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/approvals/page.tsx',
    description:
      'Registered surface /workspace/approvals. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/approvals/page.tsx.',
  },
  {
    id: 'workspace-workspace-assignments',
    domain: 'workspace',
    path: '/workspace/assignments',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/assignments/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/assignments/page.tsx',
    description:
      'Registered surface /workspace/assignments. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/assignments/page.tsx.',
  },
  {
    id: 'workspace-workspace-audit',
    domain: 'workspace',
    path: '/workspace/audit',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/audit/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/audit/page.tsx',
    description:
      'Registered surface /workspace/audit. No gateway contract is published for it; apps/web/src/app/[locale]/workspace/audit/page.tsx is the only source of truth.',
  },
  {
    id: 'workspace-workspace-cases',
    domain: 'workspace',
    path: '/workspace/cases',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/cases/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/cases/page.tsx',
    description:
      'Registered surface /workspace/cases. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/cases/page.tsx.',
  },
  {
    id: 'workspace-workspace-commerce-orders',
    domain: 'workspace',
    path: '/workspace/commerce/orders',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders. Gateway contract: POST /api/v1/commerce/orders, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-2',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}. Gateway contract: GET /api/v1/commerce/orders/{order_id}, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-cancel',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/cancel',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/cancel',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/cancel. Gateway contract: POST /api/v1/commerce/orders/{order_id}/cancel, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-confirm-payment',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/confirm-payment',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/confirm-payment',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/confirm-payment. Gateway contract: POST /api/v1/commerce/orders/{order_id}/confirm-payment, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-mark-delivered',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/mark-delivered',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/mark-delivered',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/mark-delivered. Gateway contract: POST /api/v1/commerce/orders/{order_id}/mark-delivered, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-pay',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/pay',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/pay',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/pay. Gateway contract: POST /api/v1/commerce/orders/{order_id}/pay, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-settle',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/settle',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/settle',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/settle. Gateway contract: POST /api/v1/commerce/orders/{order_id}/settle, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-ship',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/ship',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/ship',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/ship. Gateway contract: POST /api/v1/commerce/orders/{order_id}/ship, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-commerce-orders-transitions',
    domain: 'workspace',
    path: '/workspace/commerce/orders/{order_id}/transitions',
    status: 'planned',
    endpoint: '/api/v1/commerce/orders/{order_id}/transitions',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/commerce/orders/{order_id}/transitions. Gateway contract: GET /api/v1/commerce/orders/{order_id}/transitions, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-disputes',
    domain: 'workspace',
    path: '/workspace/disputes',
    status: 'planned',
    endpoint: '/api/v1/disputes',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/disputes. Gateway contract: POST /api/v1/disputes, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-disputes-2',
    domain: 'workspace',
    path: '/workspace/disputes/{dispute_id}',
    status: 'planned',
    endpoint: '/api/v1/disputes/{dispute_id}',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/disputes/{dispute_id}. Gateway contract: GET /api/v1/disputes/{dispute_id}, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-disputes-escalate',
    domain: 'workspace',
    path: '/workspace/disputes/{dispute_id}/escalate',
    status: 'planned',
    endpoint: '/api/v1/disputes/{dispute_id}/escalate',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/disputes/{dispute_id}/escalate. Gateway contract: POST /api/v1/disputes/{dispute_id}/escalate, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-disputes-resolve',
    domain: 'workspace',
    path: '/workspace/disputes/{dispute_id}/resolve',
    status: 'planned',
    endpoint: '/api/v1/disputes/{dispute_id}/resolve',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/disputes/{dispute_id}/resolve. Gateway contract: POST /api/v1/disputes/{dispute_id}/resolve, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-accounts',
    domain: 'workspace',
    path: '/workspace/finance/accounts',
    status: 'planned',
    endpoint: '/api/v1/finance/accounts',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/accounts. Gateway contract: GET /api/v1/finance/accounts, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-idempotency-keys',
    domain: 'workspace',
    path: '/workspace/finance/idempotency/keys',
    status: 'planned',
    endpoint: '/api/v1/finance/idempotency/keys',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/idempotency/keys. Gateway contract: GET /api/v1/finance/idempotency/keys, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-accounts-balance',
    domain: 'workspace',
    path: '/workspace/finance/ledger/accounts/{account_id}/balance',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/accounts/{account_id}/balance',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/accounts/{account_id}/balance. Gateway contract: GET /api/v1/finance/ledger/accounts/{account_id}/balance, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-batch',
    domain: 'workspace',
    path: '/workspace/finance/ledger/batch',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/batch',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/batch. Gateway contract: POST /api/v1/finance/ledger/batch, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-batch-post',
    domain: 'workspace',
    path: '/workspace/finance/ledger/batch/{batch_id}/post',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/batch/{batch_id}/post',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/batch/{batch_id}/post. Gateway contract: POST /api/v1/finance/ledger/batch/{batch_id}/post, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-entries',
    domain: 'workspace',
    path: '/workspace/finance/ledger/entries',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/entries',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/entries. Gateway contract: GET /api/v1/finance/ledger/entries, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-profit-and-loss',
    domain: 'workspace',
    path: '/workspace/finance/ledger/profit-and-loss',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/profit-and-loss',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/profit-and-loss. Gateway contract: GET /api/v1/finance/ledger/profit-and-loss, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-ledger-trial-balance',
    domain: 'workspace',
    path: '/workspace/finance/ledger/trial-balance',
    status: 'planned',
    endpoint: '/api/v1/finance/ledger/trial-balance',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/ledger/trial-balance. Gateway contract: GET /api/v1/finance/ledger/trial-balance, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-payments-intent',
    domain: 'workspace',
    path: '/workspace/finance/payments/intent',
    status: 'planned',
    endpoint: '/api/v1/finance/payments/intent',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/payments/intent. Gateway contract: POST /api/v1/finance/payments/intent, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-payments-webhook',
    domain: 'workspace',
    path: '/workspace/finance/payments/webhook/{provider_name}',
    status: 'planned',
    endpoint: '/api/v1/finance/payments/webhook/{provider_name}',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/payments/webhook/{provider_name}. Gateway contract: POST /api/v1/finance/payments/webhook/{provider_name}, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-reconciliation-full',
    domain: 'workspace',
    path: '/workspace/finance/reconciliation/full',
    status: 'planned',
    endpoint: '/api/v1/finance/reconciliation/full',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/reconciliation/full. Gateway contract: POST /api/v1/finance/reconciliation/full, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-reconciliation-wallet-ledger',
    domain: 'workspace',
    path: '/workspace/finance/reconciliation/wallet-ledger',
    status: 'planned',
    endpoint: '/api/v1/finance/reconciliation/wallet-ledger',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/reconciliation/wallet-ledger. Gateway contract: POST /api/v1/finance/reconciliation/wallet-ledger, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-wallet',
    domain: 'workspace',
    path: '/workspace/finance/wallet',
    status: 'planned',
    endpoint: '/api/v1/finance/wallet',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/wallet. Gateway contract: GET /api/v1/finance/wallet, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-wallet-earn',
    domain: 'workspace',
    path: '/workspace/finance/wallet/earn',
    status: 'planned',
    endpoint: '/api/v1/finance/wallet/earn',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/wallet/earn. Gateway contract: POST /api/v1/finance/wallet/earn, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-finance-wallet-redeem',
    domain: 'workspace',
    path: '/workspace/finance/wallet/redeem',
    status: 'planned',
    endpoint: '/api/v1/finance/wallet/redeem',
    method: 'POST',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /workspace/finance/wallet/redeem. Gateway contract: POST /api/v1/finance/wallet/redeem, registered in openapi.json.',
  },
  {
    id: 'workspace-workspace-knowledge',
    domain: 'workspace',
    path: '/workspace/knowledge',
    status: 'live',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/knowledge/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/knowledge/page.tsx',
    description:
      'Registered surface /workspace/knowledge. Gateway contract: GET /api/v1/content/search, registered in apps/web/src/app/[locale]/workspace/knowledge/page.tsx.',
  },
  {
    id: 'workspace-workspace-operations',
    domain: 'workspace',
    path: '/workspace/operations',
    status: 'live',
    endpoint: '/api/v1/sync/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/operations/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/operations/page.tsx',
    description:
      'Registered surface /workspace/operations. Gateway contract: GET /api/v1/sync/status, registered in apps/web/src/app/[locale]/workspace/operations/page.tsx.',
  },
  {
    id: 'workspace-workspace-operations-events',
    domain: 'workspace',
    path: '/workspace/operations/events',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/operations/events/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/operations/events/page.tsx',
    description:
      'Registered surface /workspace/operations/events. No gateway contract is published for it; apps/web/src/app/[locale]/workspace/operations/events/page.tsx is the only source of truth.',
  },
  {
    id: 'workspace-workspace-operations-jobs',
    domain: 'workspace',
    path: '/workspace/operations/jobs',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/operations/jobs/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/operations/jobs/page.tsx',
    description:
      'Registered surface /workspace/operations/jobs. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/operations/jobs/page.tsx.',
  },
  {
    id: 'workspace-workspace-overview',
    domain: 'workspace',
    path: '/workspace/overview',
    status: 'live',
    endpoint: '/api/v1/organizations',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/overview/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/overview/page.tsx',
    description:
      'Registered surface /workspace/overview. Gateway contract: GET /api/v1/organizations, registered in apps/web/src/app/[locale]/workspace/overview/page.tsx.',
  },
  {
    id: 'workspace-workspace-report-export',
    domain: 'workspace',
    path: '/workspace/report-export',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/workspaces/registry.ts',
    routeFile: null,
    description:
      'Registered surface /workspace/report-export. No gateway contract is published for it; apps/web/src/lib/workspaces/registry.ts is the only source of truth.',
  },
  {
    id: 'workspace-workspace-reports',
    domain: 'workspace',
    path: '/workspace/reports',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/reports/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/reports/page.tsx',
    description:
      'Registered surface /workspace/reports. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/reports/page.tsx.',
  },
  {
    id: 'workspace-workspace-settings',
    domain: 'workspace',
    path: '/workspace/settings',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/settings/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/settings/page.tsx',
    description:
      'Registered surface /workspace/settings. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/settings/page.tsx.',
  },
  {
    id: 'workspace-workspace-settings-access',
    domain: 'workspace',
    path: '/workspace/settings/access',
    status: 'live',
    endpoint: '/api/v1/organizations',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/settings/access/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/settings/access/page.tsx',
    description:
      'Registered surface /workspace/settings/access. Gateway contract: GET /api/v1/organizations, registered in apps/web/src/app/[locale]/workspace/settings/access/page.tsx.',
  },
  {
    id: 'workspace-workspace-settings-notifications',
    domain: 'workspace',
    path: '/workspace/settings/notifications',
    status: 'live',
    endpoint: '/api/v1/auth/notifications',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/settings/notifications/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/settings/notifications/page.tsx',
    description:
      'Registered surface /workspace/settings/notifications. Gateway contract: GET /api/v1/auth/notifications, registered in apps/web/src/app/[locale]/workspace/settings/notifications/page.tsx.',
  },
  {
    id: 'workspace-workspace-target-progress',
    domain: 'workspace',
    path: '/workspace/target-progress',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/workspaces/registry.ts',
    routeFile: null,
    description:
      'Registered surface /workspace/target-progress. No gateway contract is published for it; apps/web/src/lib/workspaces/registry.ts is the only source of truth.',
  },
  {
    id: 'workspace-workspace-targets',
    domain: 'workspace',
    path: '/workspace/targets',
    status: 'live',
    endpoint: '/api/v1/platform/health',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/targets/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/targets/page.tsx',
    description:
      'Registered surface /workspace/targets. Gateway contract: GET /api/v1/platform/health, registered in apps/web/src/app/[locale]/workspace/targets/page.tsx.',
  },
  {
    id: 'workspace-workspace-team',
    domain: 'workspace',
    path: '/workspace/team',
    status: 'live',
    endpoint: '/api/v1/organizations',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/workspace/team/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/workspace/team/page.tsx',
    description:
      'Registered surface /workspace/team. Gateway contract: GET /api/v1/organizations, registered in apps/web/src/app/[locale]/workspace/team/page.tsx.',
  },
  {
    id: 'inclusive-accessibility',
    domain: 'inclusive',
    path: '/accessibility',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/accessibility/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/accessibility/page.tsx',
    description:
      'Registered surface /accessibility. No gateway contract is published for it; apps/web/src/app/[locale]/accessibility/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-account-session',
    domain: 'inclusive',
    path: '/account/session',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/account/session/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/account/session/page.tsx',
    description:
      'Registered surface /account/session. No gateway contract is published for it; apps/web/src/app/[locale]/account/session/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-auth-2fa-status',
    domain: 'inclusive',
    path: '/auth/2fa/status',
    status: 'planned',
    endpoint: '/api/v1/auth/2fa/status',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/2fa/status. Gateway contract: GET /api/v1/auth/2fa/status, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-2fa-toggle',
    domain: 'inclusive',
    path: '/auth/2fa/toggle',
    status: 'planned',
    endpoint: '/api/v1/auth/2fa/toggle',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/2fa/toggle. Gateway contract: POST /api/v1/auth/2fa/toggle, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-account-bio',
    domain: 'inclusive',
    path: '/auth/account/bio',
    status: 'planned',
    endpoint: '/api/v1/auth/account/bio',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/account/bio. Gateway contract: POST /api/v1/auth/account/bio, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-account-status',
    domain: 'inclusive',
    path: '/auth/account/status',
    status: 'planned',
    endpoint: '/api/v1/auth/account/status',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/account/status. Gateway contract: GET /api/v1/auth/account/status, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-achievements',
    domain: 'inclusive',
    path: '/auth/achievements',
    status: 'planned',
    endpoint: '/api/v1/auth/achievements',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/achievements. Gateway contract: GET /api/v1/auth/achievements, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-activity-history',
    domain: 'inclusive',
    path: '/auth/activity/history',
    status: 'planned',
    endpoint: '/api/v1/auth/activity/history',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/activity/history. Gateway contract: GET /api/v1/auth/activity/history, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-api-keys',
    domain: 'inclusive',
    path: '/auth/api-keys',
    status: 'planned',
    endpoint: '/api/v1/auth/api-keys',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/api-keys. Gateway contract: GET /api/v1/auth/api-keys, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-api-keys-2',
    domain: 'inclusive',
    path: '/auth/api-keys/{key_id}',
    status: 'planned',
    endpoint: '/api/v1/auth/api-keys/{key_id}',
    method: 'DELETE',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/api-keys/{key_id}. Gateway contract: DELETE /api/v1/auth/api-keys/{key_id}, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-assets',
    domain: 'inclusive',
    path: '/auth/assets',
    status: 'planned',
    endpoint: '/api/v1/auth/assets',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/assets. Gateway contract: GET /api/v1/auth/assets, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-billing-subscription',
    domain: 'inclusive',
    path: '/auth/billing/subscription',
    status: 'planned',
    endpoint: '/api/v1/auth/billing/subscription',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/billing/subscription. Gateway contract: GET /api/v1/auth/billing/subscription, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-change-password',
    domain: 'inclusive',
    path: '/auth/change-password',
    status: 'planned',
    endpoint: '/api/v1/auth/change-password',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/change-password. Gateway contract: POST /api/v1/auth/change-password, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-deactivate',
    domain: 'inclusive',
    path: '/auth/deactivate',
    status: 'planned',
    endpoint: '/api/v1/auth/deactivate',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/deactivate. Gateway contract: POST /api/v1/auth/deactivate, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-email-change-confirm',
    domain: 'inclusive',
    path: '/auth/email/change-confirm',
    status: 'planned',
    endpoint: '/api/v1/auth/email/change-confirm',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/email/change-confirm. Gateway contract: POST /api/v1/auth/email/change-confirm, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-email-change-request',
    domain: 'inclusive',
    path: '/auth/email/change-request',
    status: 'planned',
    endpoint: '/api/v1/auth/email/change-request',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/email/change-request. Gateway contract: POST /api/v1/auth/email/change-request, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-export-data',
    domain: 'inclusive',
    path: '/auth/export-data',
    status: 'planned',
    endpoint: '/api/v1/auth/export-data',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/export-data. Gateway contract: POST /api/v1/auth/export-data, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-forgot-password',
    domain: 'inclusive',
    path: '/auth/forgot-password',
    status: 'planned',
    endpoint: '/api/v1/auth/forgot-password',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/forgot-password. Gateway contract: POST /api/v1/auth/forgot-password, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-legacy',
    domain: 'inclusive',
    path: '/auth/legacy',
    status: 'planned',
    endpoint: '/api/v1/auth/legacy',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/legacy. Gateway contract: GET /api/v1/auth/legacy, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-login',
    domain: 'inclusive',
    path: '/auth/login',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/auth/login/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/auth/login/page.tsx',
    description:
      'Registered surface /auth/login. No gateway contract is published for it; apps/web/src/app/[locale]/auth/login/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-auth-logout',
    domain: 'inclusive',
    path: '/auth/logout',
    status: 'planned',
    endpoint: '/api/v1/auth/logout',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/logout. Gateway contract: POST /api/v1/auth/logout, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-me',
    domain: 'inclusive',
    path: '/auth/me',
    status: 'planned',
    endpoint: '/api/v1/auth/me',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/me. Gateway contract: GET /api/v1/auth/me, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-notifications',
    domain: 'inclusive',
    path: '/auth/notifications',
    status: 'planned',
    endpoint: '/api/v1/auth/notifications',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/notifications. Gateway contract: GET /api/v1/auth/notifications, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-oauth-connect',
    domain: 'inclusive',
    path: '/auth/oauth/connect',
    status: 'planned',
    endpoint: '/api/v1/auth/oauth/connect',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/oauth/connect. Gateway contract: POST /api/v1/auth/oauth/connect, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-oauth-connections',
    domain: 'inclusive',
    path: '/auth/oauth/connections',
    status: 'planned',
    endpoint: '/api/v1/auth/oauth/connections',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/oauth/connections. Gateway contract: GET /api/v1/auth/oauth/connections, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-oauth-disconnect',
    domain: 'inclusive',
    path: '/auth/oauth/disconnect/{provider}',
    status: 'planned',
    endpoint: '/api/v1/auth/oauth/disconnect/{provider}',
    method: 'DELETE',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/oauth/disconnect/{provider}. Gateway contract: DELETE /api/v1/auth/oauth/disconnect/{provider}, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-preferences',
    domain: 'inclusive',
    path: '/auth/preferences',
    status: 'planned',
    endpoint: '/api/v1/auth/preferences',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/preferences. Gateway contract: GET /api/v1/auth/preferences, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-preferences-extended',
    domain: 'inclusive',
    path: '/auth/preferences/extended',
    status: 'planned',
    endpoint: '/api/v1/auth/preferences/extended',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/preferences/extended. Gateway contract: GET /api/v1/auth/preferences/extended, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-profile',
    domain: 'inclusive',
    path: '/auth/profile',
    status: 'planned',
    endpoint: '/api/v1/auth/profile',
    method: 'PUT',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/profile. Gateway contract: PUT /api/v1/auth/profile, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-profile-public',
    domain: 'inclusive',
    path: '/auth/profile/public',
    status: 'planned',
    endpoint: '/api/v1/auth/profile/public',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/profile/public. Gateway contract: GET /api/v1/auth/profile/public, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-rate-limit',
    domain: 'inclusive',
    path: '/auth/rate-limit',
    status: 'planned',
    endpoint: '/api/v1/auth/rate-limit',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/auth.py',
    routeFile: null,
    description:
      'Registered surface /auth/rate-limit. Gateway contract: GET /api/v1/auth/rate-limit, registered in services/api_gateway/routers/auth.py.',
  },
  {
    id: 'inclusive-auth-signup',
    domain: 'inclusive',
    path: '/auth/signup',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/auth/signup/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/auth/signup/page.tsx',
    description:
      'Registered surface /auth/signup. No gateway contract is published for it; apps/web/src/app/[locale]/auth/signup/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-inclusive-sms-delivery-receipt',
    domain: 'inclusive',
    path: '/inclusive/sms-delivery-receipt',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /inclusive/sms-delivery-receipt. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'inclusive-inclusive-ussd-session-audit',
    domain: 'inclusive',
    path: '/inclusive/ussd-session-audit',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /inclusive/ussd-session-audit. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'inclusive-inclusive-voice-call-record',
    domain: 'inclusive',
    path: '/inclusive/voice-call-record',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/domains/registry.ts',
    routeFile: null,
    description:
      'Registered surface /inclusive/voice-call-record. No gateway contract is published for it; apps/web/src/lib/domains/registry.ts is the only source of truth.',
  },
  {
    id: 'inclusive-offline',
    domain: 'inclusive',
    path: '/offline',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/offline/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/offline/page.tsx',
    description:
      'Registered surface /offline. No gateway contract is published for it; apps/web/src/app/[locale]/offline/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-simple',
    domain: 'inclusive',
    path: '/simple',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/simple/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/simple/page.tsx',
    description:
      'Registered surface /simple. No gateway contract is published for it; apps/web/src/app/[locale]/simple/page.tsx is the only source of truth.',
  },
  {
    id: 'inclusive-telecom',
    domain: 'inclusive',
    path: '/telecom',
    status: 'live',
    endpoint: '/api/v1/ussd/status',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/telecom/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/telecom/page.tsx',
    description:
      'Registered surface /telecom. Gateway contract: GET /api/v1/ussd/status, registered in apps/web/src/app/[locale]/telecom/page.tsx.',
  },
  {
    id: 'learning-learn',
    domain: 'learning',
    path: '/learn',
    status: 'live',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/learn/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/learn/page.tsx',
    description:
      'Registered surface /learn. Gateway contract: GET /api/v1/content/search, registered in apps/web/src/app/[locale]/learn/page.tsx.',
  },
  {
    id: 'learning-learn-assessment-submission',
    domain: 'learning',
    path: '/learn/assessment-submission',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/assessment-submission. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-learn-certificate-verify',
    domain: 'learning',
    path: '/learn/certificate-verify',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/certificate-verify. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-learn-content-search',
    domain: 'learning',
    path: '/learn/content/search',
    status: 'planned',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/content_public.py',
    routeFile: null,
    description:
      'Registered surface /learn/content/search. Gateway contract: GET /api/v1/content/search, registered in services/api_gateway/routers/content_public.py.',
  },
  {
    id: 'learning-learn-course-enrolment',
    domain: 'learning',
    path: '/learn/course-enrolment',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/course-enrolment. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-learn-legal',
    domain: 'learning',
    path: '/learn/legal',
    status: 'planned',
    endpoint: '/api/v1/legal-texts',
    method: 'GET',
    sourceOfTruth: 'openapi.json',
    routeFile: null,
    description:
      'Registered surface /learn/legal. Gateway contract: GET /api/v1/legal-texts, registered in openapi.json.',
  },
  {
    id: 'learning-learn-legal-locales',
    domain: 'learning',
    path: '/learn/legal/locales',
    status: 'planned',
    endpoint: '/api/v1/legal-texts/locales',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/legal_texts.py',
    routeFile: null,
    description:
      'Registered surface /learn/legal/locales. Gateway contract: GET /api/v1/legal-texts/locales, registered in services/api_gateway/routers/legal_texts.py.',
  },
  {
    id: 'learning-learn-legal-slugs',
    domain: 'learning',
    path: '/learn/legal/slugs',
    status: 'planned',
    endpoint: '/api/v1/legal-texts/slugs',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/legal_texts.py',
    routeFile: null,
    description:
      'Registered surface /learn/legal/slugs. Gateway contract: GET /api/v1/legal-texts/slugs, registered in services/api_gateway/routers/legal_texts.py.',
  },
  {
    id: 'learning-learn-legal-2',
    domain: 'learning',
    path: '/learn/legal/{locale}/{slug}',
    status: 'planned',
    endpoint: '/api/v1/legal-texts/{locale}/{slug}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/legal_texts.py',
    routeFile: null,
    description:
      'Registered surface /learn/legal/{locale}/{slug}. Gateway contract: GET /api/v1/legal-texts/{locale}/{slug}, registered in services/api_gateway/routers/legal_texts.py.',
  },
  {
    id: 'learning-learn-legal-versions',
    domain: 'learning',
    path: '/learn/legal/{locale}/{slug}/versions',
    status: 'planned',
    endpoint: '/api/v1/legal-texts/{locale}/{slug}/versions',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/legal_texts.py',
    routeFile: null,
    description:
      'Registered surface /learn/legal/{locale}/{slug}/versions. Gateway contract: GET /api/v1/legal-texts/{locale}/{slug}/versions, registered in services/api_gateway/routers/legal_texts.py.',
  },
  {
    id: 'learning-learn-legal-3',
    domain: 'learning',
    path: '/learn/legal/{locale}/{slug}/{version}',
    status: 'planned',
    endpoint: '/api/v1/legal-texts/{locale}/{slug}/{version}',
    method: 'PATCH',
    sourceOfTruth: 'services/api_gateway/routers/legal_texts.py',
    routeFile: null,
    description:
      'Registered surface /learn/legal/{locale}/{slug}/{version}. Gateway contract: PATCH /api/v1/legal-texts/{locale}/{slug}/{version}, registered in services/api_gateway/routers/legal_texts.py.',
  },
  {
    id: 'learning-learn-library-checkout',
    domain: 'learning',
    path: '/learn/library-checkout',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/library-checkout. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-learn-manual-climate-normals',
    domain: 'learning',
    path: '/learn/manual/climate-normals/{site_id}',
    status: 'planned',
    endpoint: '/api/v1/manual/climate-normals/{site_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/climate-normals/{site_id}. Gateway contract: GET /api/v1/manual/climate-normals/{site_id}, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-crop-calendar',
    domain: 'learning',
    path: '/learn/manual/crop-calendar',
    status: 'planned',
    endpoint: '/api/v1/manual/crop-calendar',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/crop-calendar. Gateway contract: GET /api/v1/manual/crop-calendar, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-crop-params',
    domain: 'learning',
    path: '/learn/manual/crop-params',
    status: 'planned',
    endpoint: '/api/v1/manual/crop-params',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/crop-params. Gateway contract: GET /api/v1/manual/crop-params, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-sites',
    domain: 'learning',
    path: '/learn/manual/sites',
    status: 'planned',
    endpoint: '/api/v1/manual/sites',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/sites. Gateway contract: GET /api/v1/manual/sites, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-sites-2',
    domain: 'learning',
    path: '/learn/manual/sites/{site_id}',
    status: 'planned',
    endpoint: '/api/v1/manual/sites/{site_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/sites/{site_id}. Gateway contract: GET /api/v1/manual/sites/{site_id}, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-soil-regions',
    domain: 'learning',
    path: '/learn/manual/soil-regions',
    status: 'planned',
    endpoint: '/api/v1/manual/soil-regions',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/soil-regions. Gateway contract: GET /api/v1/manual/soil-regions, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-status',
    domain: 'learning',
    path: '/learn/manual/status',
    status: 'planned',
    endpoint: '/api/v1/manual/status',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/status. Gateway contract: GET /api/v1/manual/status, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-manual-weather-daily',
    domain: 'learning',
    path: '/learn/manual/weather-daily/{site_id}',
    status: 'planned',
    endpoint: '/api/v1/manual/weather-daily/{site_id}',
    method: 'GET',
    sourceOfTruth: 'services/api_gateway/routers/manual_data.py',
    routeFile: null,
    description:
      'Registered surface /learn/manual/weather-daily/{site_id}. Gateway contract: GET /api/v1/manual/weather-daily/{site_id}, registered in services/api_gateway/routers/manual_data.py.',
  },
  {
    id: 'learning-learn-newsletter-subscribe',
    domain: 'learning',
    path: '/learn/newsletter/subscribe',
    status: 'planned',
    endpoint: '/api/v1/newsletter/subscribe',
    method: 'POST',
    sourceOfTruth: 'services/api_gateway/routers/newsletter.py',
    routeFile: null,
    description:
      'Registered surface /learn/newsletter/subscribe. Gateway contract: POST /api/v1/newsletter/subscribe, registered in services/api_gateway/routers/newsletter.py.',
  },
  {
    id: 'learning-learn-video-caption-pack',
    domain: 'learning',
    path: '/learn/video-caption-pack',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/video-caption-pack. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-learn-video-progress',
    domain: 'learning',
    path: '/learn/video-progress',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
    routeFile: null,
    description:
      'Registered surface /learn/video-progress. No gateway contract is published for it; apps/web/src/lib/api/market.ts is the only source of truth.',
  },
  {
    id: 'learning-public-education-advanced-search',
    domain: 'learning',
    path: '/public/education/advanced-search',
    status: 'live',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/advanced-search/page.tsx',
    routeFile: null,
    description:
      'Registered surface /public/education/advanced-search. Gateway contract: GET /api/v1/content/search, registered in apps/web/src/app/[locale]/public/education/advanced-search/page.tsx.',
  },
  {
    id: 'learning-public-education-certifications',
    domain: 'learning',
    path: '/public/education/certifications',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/certifications/page.tsx',
    routeFile: null,
    description:
      'Registered surface /public/education/certifications. No gateway contract is published for it; apps/web/src/app/[locale]/public/education/certifications/page.tsx is the only source of truth.',
  },
  {
    id: 'learning-public-education-courses',
    domain: 'learning',
    path: '/public/education/courses',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/courses/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/courses/page.tsx',
    description:
      'Registered surface /public/education/courses. No gateway contract is published for it; apps/web/src/app/[locale]/public/education/courses/page.tsx is the only source of truth.',
  },
  {
    id: 'learning-public-education-glossary',
    domain: 'learning',
    path: '/public/education/glossary',
    status: 'live',
    endpoint: '/api/v1/science/agrovoc',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/glossary/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/glossary/page.tsx',
    description:
      'Registered surface /public/education/glossary. Gateway contract: GET /api/v1/science/agrovoc, registered in apps/web/src/app/[locale]/public/education/glossary/page.tsx.',
  },
  {
    id: 'learning-public-education-library',
    domain: 'learning',
    path: '/public/education/library',
    status: 'live',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/library/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/library/page.tsx',
    description:
      'Registered surface /public/education/library. Gateway contract: GET /api/v1/content/search, registered in apps/web/src/app/[locale]/public/education/library/page.tsx.',
  },
  {
    id: 'learning-public-education-library-advanced',
    domain: 'learning',
    path: '/public/education/library-advanced',
    status: 'live',
    endpoint: '/api/v1/content/search',
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/library-advanced/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/library-advanced/page.tsx',
    description:
      'Registered surface /public/education/library-advanced. Gateway contract: GET /api/v1/content/search, registered in apps/web/src/app/[locale]/public/education/library-advanced/page.tsx.',
  },
  {
    id: 'learning-public-education-video-player',
    domain: 'learning',
    path: '/public/education/video-player',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/video-player/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/video-player/page.tsx',
    description:
      'Registered surface /public/education/video-player. No gateway contract is published for it; apps/web/src/app/[locale]/public/education/video-player/page.tsx is the only source of truth.',
  },
  {
    id: 'learning-public-education-workshops',
    domain: 'learning',
    path: '/public/education/workshops',
    status: 'unavailable',
    endpoint: null,
    method: 'GET',
    sourceOfTruth: 'apps/web/src/app/[locale]/public/education/workshops/page.tsx',
    routeFile: 'apps/web/src/app/[locale]/public/education/workshops/page.tsx',
    description:
      'Registered surface /public/education/workshops. No gateway contract is published for it; apps/web/src/app/[locale]/public/education/workshops/page.tsx is the only source of truth.',
  },
];

/**
 * Resolve the page file for a catalogue path by looking on disk.
 *
 * The declared `routeFile` in `SEEDS` is what the catalogue *claims*; this is
 * what actually exists. Preferring the filesystem is what keeps the two from
 * drifting, and it removes a whole failure mode: a generator that rewrites 600
 * entries by regular expression can silently truncate the file, and it did so
 * twice before this was changed.
 *
 * `{id}` in a catalogue path is a route parameter and `[id]` on disk. A path that
 * names a param therefore resolves to any page whose route matches the shape,
 * which is what `routeFileFor` below checks.
 */
function resolveRouteFile(path: string, declared: string | null): string | null {
  if (declared) {
    // A declared file is only trusted when it is actually there.
    try {
      statSync(join(REPO_ROOT, declared));
      return declared;
    } catch {
      // Fall through to the filesystem scan.
    }
  }
  return routeFileFor(path);
}

const ROUTE_FILE_CACHE = new Map<string, string | null>();

/** Every `page.tsx` under the locale tree, as catalogue-shaped paths. */
function realRouteFiles(): readonly string[] {
  if (realRouteFiles.cached) return realRouteFiles.cached;
  const files: string[] = [];
  const walk = (dir: string) => {
    let entries: import('node:fs').Dirent[];
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
        files.push(
          relative(REPO_ROOT, full)
            .split(sep)
            .join('/')
            .replace('apps/web/src/app/[locale]', '')
            .replace('/page.tsx', '') || '/',
        );
      }
    }
  };
  walk(join(REPO_ROOT, 'apps', 'web', 'src', 'app', '[locale]'));
  realRouteFiles.cached = files;
  return files;
}
realRouteFiles.cached = undefined as unknown as string[];

/**
 * Route-directory name aliases.
 *
 * The catalogue names a parameter `{site_id}`; the directory on disk is
 * `[siteId]`. Matching on names alone left three learning-manual entries looking
 * unrouted, and each was then a fallback path that the real `[siteId]` page
 * silently swallowed.
 *
 * Matching on *shape* instead was tried and rejected: seventy-four catalogue
 * paths are dynamic and the app has fewer dynamic directories, so shape-matching
 * let many entries claim a hand-written page that serves a different logical
 * path. Three explicit aliases say what is meant; a loose comparison says
 * something nobody decided.
 */
const ROUTE_DIR_ALIASES: Record<string, string> = {
  site_id: 'siteId',
};

/** Does a real route file serve this catalogue path? */
function routeFileFor(path: string): string | null {
  if (ROUTE_FILE_CACHE.has(path)) return ROUTE_FILE_CACHE.get(path) ?? null;

  const aliased = path.replace(
    /\{(\w+)\}/g,
    (_match, name: string) => `{${ROUTE_DIR_ALIASES[name] ?? name}}`,
  );

  const literal = `apps/web/src/app/[locale]${aliased === '/' ? '' : aliased}/page.tsx`;
  try {
    statSync(join(REPO_ROOT, literal));
    ROUTE_FILE_CACHE.set(path, literal);
    return literal;
  } catch {
    // Not a static route. Try a parameterised one.
  }

  for (const file of realRouteFiles()) {
    const logical = file
      .replace(/^\[\.\.\.(\w+)\]$/, '')
      .replace(/\[\.\.\.(\w+)\]/g, '{$1}')
      .replace(/\[(\w+)\]/g, '{$1}');
    if (
      logical === path ||
      logical === aliased ||
      logical === `${path}/` ||
      logical === `${aliased}/`
    ) {
      const full = `apps/web/src/app/[locale]${file}/page.tsx`;
      ROUTE_FILE_CACHE.set(path, full);
      return full;
    }
  }

  ROUTE_FILE_CACHE.set(path, null);
  return null;
}

function buildEntry(seed: CatalogSeed, group: (typeof CATALOG_GROUPS)[number]): CatalogEntry {
  const routeFile = resolveRouteFile(seed.path, seed.routeFile);
  const hasRoute = routeFile !== null;
  const registryDriven = seed.path.includes('{');
  const status = resolveCatalogStatus({
    endpoint: seed.endpoint,
    hasRoute,
    registryDriven,
    declaredContent: isDeclaredStatic(seed.path),
  });
  const renderedBy: CatalogEntry['renderedBy'] = hasRoute
    ? 'route'
    : isReservedPath(seed.path)
      ? 'marketplace-catchall'
      : 'catalog-catchall';
  return {
    id: seed.id,
    path: seed.path,
    domain: group.domain,
    status,
    endpoint: seed.endpoint,
    method: seed.method,
    sourceOfTruth: seed.sourceOfTruth,
    owner: group.owner,
    gate: group.gate,
    access: seed.access ?? group.access,
    routeFile,
    renderedBy,
    indexable: resolveIndexable(status),
    description: seed.description,
  };
}

export const PAGE_CATALOG: readonly CatalogEntry[] = SEEDS.map((seed) => {
  const group = CATALOG_GROUPS.find((candidate) => candidate.domain === seed.domain);
  if (!group) throw new Error(`unknown catalog domain: ${seed.domain}`);
  return buildEntry(seed, group);
});

const BY_PATH = new Map(PAGE_CATALOG.map((entry) => [entry.path, entry]));

export function getCatalogEntry(path: string): CatalogEntry | undefined {
  return BY_PATH.get(path);
}

export function getCatalogEntryById(id: string): CatalogEntry | undefined {
  return PAGE_CATALOG.find((entry) => entry.id === id);
}

export function getCatalogGroup(domain: CatalogDomain) {
  return CATALOG_GROUPS.find((group) => group.domain === domain);
}

export function catalogByDomain(domain: CatalogDomain): readonly CatalogEntry[] {
  return PAGE_CATALOG.filter((entry) => entry.domain === domain);
}

/**
 * Paths this catalog is allowed to render. Anything already routed stays with
 * its own page, and `/market/**` stays with the marketplace catch-all, so the
 * catalog route can never duplicate an existing page.
 */
export function catalogFallbackPaths(): readonly string[] {
  return PAGE_CATALOG.filter((entry) => entry.renderedBy === 'catalog-catchall').map(
    (entry) => entry.path,
  );
}

/** `generateStaticParams` payload for the catalog catch-all. */
export function catalogFallbackParams(): { slug: string[] }[] {
  const seen = new Set<string>();
  const params: { slug: string[] }[] = [];
  for (const path of catalogFallbackPaths()) {
    if (path.includes('{')) continue;
    const slug = path.replace(/^\//, '').split('/');
    const key = slug.join('/');
    if (seen.has(key)) continue;
    seen.add(key);
    params.push({ slug });
  }
  return params;
}

/** Resolves a `slug` catch-all param to its catalog entry. */
export function getCatalogEntryForSlug(slug: readonly string[]): CatalogEntry | undefined {
  return getCatalogEntry(`/${slug.join('/')}`);
}

export const CATALOG_STATUS_TOTALS = PAGE_CATALOG.reduce<Record<CatalogStatus, number>>(
  (totals, entry) => {
    totals[entry.status] += 1;
    return totals;
  },
  { live: 0, capability: 0, static: 0, planned: 0, unavailable: 0 },
);
