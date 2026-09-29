export const ROUTE_MANIFEST_VERSION = '2026-09-26';

export const PLANNING_CEILING = 987;
/**
 * Measured by scanning `src/app` for every `page.tsx`.
 *
 * This constant sat at 175 while the real count was 241, because nothing compared
 * it to disk, and it drifted again to 352 as pages were generated from the
 * catalogue. The assertion in `route-manifest.test.ts` is what makes that
 * impossible: the number in the source is a claim, and the assertion is the
 * check.
 *
 * The figure is the whole tree. `page-catalog.test.ts` scans the same tree for
 * routable pages, excluding the catalogue catch-all and `_not-found`.
 */
export const CURRENT_PAGE_FILES_OBSERVED = 352;

export type RouteContext =
  | 'public'
  | 'marketplace'
  | 'hydroma'
  | 'admin'
  | 'research'
  | 'system'
  | 'assistant'
  | 'message-templates';

export type RouteMaturity = 'scaffold' | 'alpha' | 'beta' | 'ga' | 'deprecated';
export type AccessLevel = 'public' | 'authenticated' | 'role-gated' | 'internal';

export interface RouteManifestEntry {
  id: string;
  pattern: string;
  context: RouteContext;
  plannedPages: number;
  maturity: RouteMaturity;
  access: AccessLevel;
  owner: string;
  api: string;
  i18n: string;
  tests: string[];
  sourceOfTruth: string;
  notes: string;
}

export const routeManifest = [
  {
    id: 'public',
    pattern: '/:locale/public/**',
    context: 'public',
    plannedPages: 70,
    maturity: 'beta',
    access: 'public',
    owner: 'content-platform',
    api: 'public-api',
    i18n: 'public',
    tests: ['public-contract', 'a11y', 'i18n', 'metadata'],
    sourceOfTruth: 'master-plan/public-context',
    notes: 'Public home, evidence, services, legal, education and channel pages.',
  },
  {
    id: 'marketplace',
    pattern: '/:locale/market/**',
    context: 'marketplace',
    plannedPages: 444,
    maturity: 'alpha',
    access: 'public',
    owner: 'marketplace',
    api: 'marketplace-api',
    i18n: 'market',
    tests: ['contract', 'escrow', 'auth', 'e2e', 'security'],
    sourceOfTruth: 'master-plan/marketplace-context',
    notes: 'Build one real product-to-escrow vertical before template expansion.',
  },
  {
    id: 'hydroma',
    pattern: '/:locale/hydroma/**',
    context: 'hydroma',
    plannedPages: 174,
    maturity: 'scaffold',
    access: 'public',
    owner: 'hydroma',
    api: 'hydroma-tools-api',
    i18n: 'hydroma',
    tests: ['schema', 'replay', 'provenance', 'performance', 'e2e'],
    sourceOfTruth: 'master-plan/hydroma-context',
    notes: 'Tool registry, execute/replay, uncertainty, OGC and offline fallback.',
  },
  {
    id: 'admin',
    pattern: '/:locale/admin/**',
    context: 'admin',
    plannedPages: 134,
    maturity: 'scaffold',
    access: 'role-gated',
    owner: 'platform-admin',
    api: 'admin-api',
    i18n: 'admin',
    tests: ['authz', 'audit', 'security', 'e2e'],
    sourceOfTruth: 'master-plan/admin-context',
    notes: 'No page may be enabled without deny-by-default server authorization.',
  },
  {
    id: 'research',
    pattern: '/:locale/research/**',
    context: 'research',
    plannedPages: 72,
    maturity: 'scaffold',
    access: 'authenticated',
    owner: 'research-platform',
    api: 'research-api',
    i18n: 'research',
    tests: ['authz', 'reproducibility', 'contract', 'e2e'],
    sourceOfTruth: 'master-plan/research-context',
    notes: 'Datasets, experiments, saved runs, citations and approval workflows.',
  },
  {
    id: 'system',
    pattern: '/:locale/system/**',
    context: 'system',
    plannedPages: 30,
    maturity: 'scaffold',
    access: 'internal',
    owner: 'platform-operations',
    api: 'operations-api',
    i18n: 'system',
    tests: ['health', 'security', 'telemetry', 'e2e'],
    sourceOfTruth: 'master-plan/system-context',
    notes: 'Health, data quality, queues, migrations, incidents and integrations.',
  },
  {
    id: 'assistant',
    pattern: '/:locale/ai/**',
    context: 'assistant',
    plannedPages: 20,
    maturity: 'scaffold',
    access: 'authenticated',
    owner: 'assistant-platform',
    api: 'assistant-api',
    i18n: 'ai',
    tests: ['citations', 'prompt-injection', 'privacy', 'e2e'],
    sourceOfTruth: 'master-plan/assistant-context',
    notes: 'Citation-first answers, tool allowlists and human approval.',
  },
  {
    id: 'message-templates',
    pattern: '/:locale/developers/message-templates/**',
    context: 'message-templates',
    plannedPages: 43,
    maturity: 'scaffold',
    access: 'role-gated',
    owner: 'content-platform',
    api: 'template-api',
    i18n: 'developers',
    tests: ['schema', 'localization', 'permissions', 'e2e'],
    sourceOfTruth: 'master-plan/message-template-context',
    notes: 'Versioned multilingual templates with preview, approval and rollback.',
  },
] as const satisfies readonly RouteManifestEntry[];

export const plannedPageTotal = routeManifest.reduce(
  (total, entry) => total + entry.plannedPages,
  0,
);

export function getRouteManifestEntry(id: string): RouteManifestEntry | undefined {
  return routeManifest.find((entry) => entry.id === id);
}

export function isRouteContext(value: string): value is RouteContext {
  return routeManifest.some((entry) => entry.context === value);
}
