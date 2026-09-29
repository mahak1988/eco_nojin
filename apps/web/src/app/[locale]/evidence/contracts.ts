/**
 * The contract table behind `/evidence` and `/references`.
 *
 * Both pages answer the same question — "where did this number come from?" — and
 * the honest answer for each figure differs in kind:
 *
 *   - a **live** read returns a number the gateway produced now, and the stamp
 *     is `verified`;
 *   - a **derived** figure is computed here from a live response (a sum, a
 *     difference, a count of what is present), and the stamp says which response
 *     it came from rather than claiming a contract of its own;
 *   - an **absent** capability has no contract at all, and the page says what
 *     contract would create it.
 *
 * The three kinds are declared here rather than decided per call site, because a
 * page that mixes them without saying so is exactly how a derived number ends up
 * looking like a measured one.
 */

export type ContractKind = 'live' | 'derived' | 'absent';

export interface ContractRow {
  /** Stable id, used as a React key and as the row's own label. */
  readonly id: string;
  /** The published path, or the path a capability would need. */
  readonly path: string;
  readonly kind: ContractKind;
  /** Which response a `derived` row is computed from. */
  readonly derivedFrom?: string;
  /** The router file that decides what this surface may show. */
  readonly source: string;
}

/** Every read the two pages make, in the order they are fetched. */
export const INTEGRITY_CONTRACTS: readonly ContractRow[] = [
  {
    id: 'citations',
    path: '/api/v1/science/citations/index',
    kind: 'live',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'datasets',
    path: '/api/v1/science/datasets',
    kind: 'live',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'model-cards',
    path: '/api/v1/science/model-cards',
    kind: 'live',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'agrovoc',
    path: '/api/v1/science/agrovoc',
    kind: 'live',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'zenodo',
    path: '/api/v1/science/zenodo/status',
    kind: 'live',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'validation',
    path: '/api/v1/hydroma/validation',
    kind: 'live',
    source: 'services/api_gateway/routers/hydroma_ops.py',
  },
  {
    id: 'external-validation',
    path: 'GET /api/v1/science/external-validation',
    kind: 'absent',
    source: 'services/api_gateway/routers/science.py',
  },
  {
    id: 'external-doi',
    path: 'GET /api/v1/science/dois',
    kind: 'absent',
    source: 'services/api_gateway/routers/science.py',
  },
];

/**
 * The aspirations the master plan's §7 rule names: "no external validation
 * claim". Each is a thing a reader of an evidence page would reasonably expect
 * to find, and each is absent because nothing in this repository records it.
 * `contract` is the read that would create it.
 */
export const ASPIRATIONS: readonly { readonly id: string; readonly contract: string }[] = [
  { id: 'external-validation', contract: 'GET /api/v1/science/external-validation' },
  { id: 'external-doi', contract: 'GET /api/v1/science/dois' },
  { id: 'peer-review', contract: 'GET /api/v1/science/peer-review' },
];

export type CitationIndex = {
  count: number;
  items: {
    slug: string;
    name_en?: string | null;
    name_fa?: string | null;
    reference?: string | null;
    doi?: string | null;
  }[];
};

export type DatasetCatalog = {
  count: number;
  live: number;
  datasets: {
    id: string;
    name: string;
    domain: string;
    source: string;
    status: string;
    requires: string;
    license: string;
  }[];
};

export type ModelCards = {
  cards?: { slug: string; [key: string]: unknown }[];
  count?: number;
};

export type Agrovoc = {
  count: number | null;
  results: { term?: string; definition?: string; uri?: string }[];
  stats: { total?: number; languages?: number; [key: string]: unknown };
};

export type ZenodoStatus = { configured: boolean; status: string };
