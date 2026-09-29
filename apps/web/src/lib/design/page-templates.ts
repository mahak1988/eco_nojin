import type { ReactNode } from 'react';

import type { DataState, StateLabels } from '@/components/ui/StateSlot';
import type { CatalogDomain, CatalogEntry } from '@/lib/domains/page-catalog';

/**
 * The twelve page templates of the master plan, as a type-checked registry.
 *
 * The plan's own gap table (row 6) records the defect this file exists to fix:
 * "۱۱۰ صفحهٔ مدل علمی تک‌الگو — خستگی کاربر، تکرار". In this tree every
 * catalogue-driven page renders through one `ResourcePage` component, so a
 * 110-page scientific surface and a bazaar list are literally the same layout.
 * The plan answers with twelve named archetypes (§4.4) and per-context
 * assignments (§6).
 *
 * What this module adds to a list of names is the part that was missing: a
 * template is *enforced*, not remembered.
 *
 *   - Every template declares the five states of §4.5, and the declaration is a
 *     five-element tuple, so a template that drops `partial` does not compile.
 *   - Every template carries a `provenance` requirement typed to the literal
 *     region `'provenance'`, so the plan's "مُهر منبع روی هر عدد" is a property
 *     of the type rather than a review comment.
 *   - Every template claims its surfaces through a predicate over the real
 *     catalogue entry, and `matchTemplates` is tested for being a *partition*:
 *     each of the 600 routes lands in exactly one template. A new route that
 *     matches nothing fails the suite by name.
 *
 * Text is never invented here. A template declares which regions exist and what
 * a reader can do on the surface; the caller supplies every label through
 * `TemplateLabels`, resolved from `messages/<locale>.json`.
 */

/* -------------------------------------------------------------------------- */
/*  Plan vocabulary                                                           */
/* -------------------------------------------------------------------------- */

/** The twelve ids of §4.4, in plan order. Asserted to have length 12. */
export const TEMPLATE_IDS = [
  'cover',
  'narrative',
  'discovery',
  'detail',
  'flow',
  'dashboard',
  'instrument',
  'ledger',
  'legal',
  'report',
  'system',
  'learning',
] as const;

export type TemplateId = (typeof TEMPLATE_IDS)[number];

/** Plan code as written in §4.4, T01–T12. Carried so a note can cite it. */
export type PlanCode = `T${number}`;

/* -------------------------------------------------------------------------- */
/*  Regions                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * The regions a page surface can be built from, named as layout units rather
 * than as components, so a template describes a page rather than an
 * implementation.
 *
 * `'provenance'` is one of the twelve and not an optional extra: §2(1) of the
 * plan preserves the standing rule that a page shows real data or an explicit
 * label, and §4.1 makes the source stamp on every number the platform's memory.
 * `ProvenanceRequirement` below is what keeps that from being a convention.
 */
export type RequiredRegion =
  /** `<h1>` plus the lead paragraph. */
  | 'title'
  /** Live/unavailable badge for the underlying contract. */
  | 'status'
  /** The source stamp. Mandatory on every template. */
  | 'provenance'
  /** Search, filter and sort header. */
  | 'filters'
  /** The five-state slot. Mandatory on every template. */
  | 'state'
  /** Where the response is rendered: table, record, grid, map or chart. */
  | 'data'
  /** Tabs, a side rail, or a stepper. */
  | 'navigation'
  /** The one thing the reader came to do. */
  | 'actions'
  /** A standing summary beside the data. */
  | 'summary'
  /** Expandable detail or a documentation drawer. */
  | 'detail'
  /** Supporting narrative under the data. */
  | 'notes'
  /** Print header and document download. */
  | 'print'
  /** Legal links, version and the catalogue slug. */
  | 'footer';

/** Regions no template may omit, whatever its purpose. */
export const MANDATORY_REGIONS = [
  'title',
  'status',
  'provenance',
  'state',
  'data',
  'footer',
] as const satisfies readonly RequiredRegion[];

/**
 * The plan's own note in §4.1: a 14px source/date stamp on every number. This
 * says *where* the stamp anchors on a given template, so "every number" is a
 * placement decision rather than an aspiration. `'provenance'` means the stamp
 * stands on its own rather than hanging off a data, summary, detail or action
 * region.
 */
export type ProvenanceAnchor = 'provenance' | 'data' | 'summary' | 'detail' | 'actions';

export interface ProvenanceRequirement {
  /**
   * Literal `provenance`, so a template cannot satisfy this by naming a
   * different region. The type is the enforcement; the tests then confirm all
   * twelve really carry it.
   */
  readonly region: 'provenance';
  /** The region the stamp is attached to on this template. */
  readonly anchor: ProvenanceAnchor;
  /** Always `true`; present so a template's declaration is self-describing. */
  readonly required: true;
}

/* -------------------------------------------------------------------------- */
/*  States                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * The five states of §4.5 that a data-bearing surface must be able to show.
 *
 * `DataState` also carries `'ready'`; the plan's requirement is the other five,
 * because a page that is showing data is not in one of these states. Modelling
 * the declaration as a five-element tuple means a template that forgot
 * `partial` is a compile error, not a page that quietly presents a truncated
 * answer as a complete one.
 */
export const REQUIRED_STATES = ['loading', 'empty', 'error', 'partial', 'offline'] as const;

export type RequiredState = (typeof REQUIRED_STATES)[number];

/** Exactly the five, in §4.5 order. Fewer or more does not type-check. */
export type PageStateCoverage = readonly [
  RequiredState,
  RequiredState,
  RequiredState,
  RequiredState,
  RequiredState,
];

/* -------------------------------------------------------------------------- */
/*  Density and primary action                                                */
/* -------------------------------------------------------------------------- */

/**
 * The plan's triple density (§4.1), named for what it means rather than for the
 * `CardDensity` literal it maps onto: `comfortable` is `cozy`, `compact` is
 * `compact`, `dense` is `dense`. Density is the plan's answer to a dense
 * surface, and the plan itself pairs it with a context — compact for the
 * marketplace and admin, dense for the scientific table.
 */
export type PageDensity = 'comfortable' | 'compact' | 'dense';

/** What the primary action actually does, so a caller can label it correctly. */
export type PrimaryActionKind =
  /** Move to another surface. */
  | 'navigate'
  /** Commit a form. */
  | 'submit'
  /** Re-run a model or query. */
  | 'run'
  /** Re-fetch after a failure. */
  | 'retry'
  /** Narrow a list. */
  | 'filter'
  /** Produce a document. */
  | 'print'
  /** Produce a file. */
  | 'export';

export interface PrimaryAction {
  /** Where it sits. Always `actions`; a template cannot float it. */
  readonly region: 'actions';
  readonly kind: PrimaryActionKind;
  /** Plain-language purpose, reported by the tests. Not user-visible copy. */
  readonly purpose: string;
}

/* -------------------------------------------------------------------------- */
/*  Route shape                                                               */
/* -------------------------------------------------------------------------- */

/**
 * The signals a predicate is allowed to read.
 *
 * Templates are matched over the *shape* of a route rather than over its exact
 * path where possible, so a new `hydroma/tools/<name>/execute` inherits T07
 * without a new rule. Where a shape is genuinely route-specific the predicate
 * names the paths it claims, and the test reports which entries landed there.
 */
export interface RouteContext {
  readonly entry: CatalogEntry;
  readonly path: string;
  readonly domain: CatalogDomain;
  /** Path split on `/`, with the locale slot removed. `/` is `[]`. */
  readonly segments: readonly string[];
  /** Last segment, or `''` for the root. */
  readonly leaf: string;
  readonly depth: number;
  /** A `{id}` or `{*segments}` segment is present. */
  readonly hasParam: boolean;
  /** The leaf is a wizard step: `step3`, `3`. */
  readonly isStep: boolean;
  /**
   * The route writes: either the leaf names a write, or the catalogue declares a
   * method other than `GET`. 168 of the 600 entries are writes, and a write is
   * a form rather than a read — which is what puts it on T05.
   */
  readonly isCommand: boolean;
  /** The route is an invocation of a registered tool. */
  readonly isTool: boolean;
}

export type RoutePredicate = (context: RouteContext) => boolean;

/**
 * Path segments that name a write even when the catalogue says `GET`.
 *
 * The catalogue's `method` is the contract's method, and 168 entries are writes;
 * this set catches the ones it misses, so a read-shaped leaf that is really a
 * verb is not mistaken for a record.
 */
const WRITE_LEAVES = new Set([
  'activate',
  'ack',
  'approve',
  'cancel-schedule',
  'complete',
  'confirm',
  'confirm-payment',
  'connect',
  'create',
  'disconnect',
  'distribute',
  'earn',
  'engage',
  'engaged',
  'enrol',
  'enroll',
  'escalate',
  'execute',
  'export-data',
  'generate-draft',
  'interest',
  'load',
  'mark-delivered',
  'pay',
  'post',
  'provision-qr',
  'publish',
  'pull',
  'redeem',
  'refresh-data',
  'register',
  'request',
  'resolve',
  'restart',
  'retire',
  'run',
  'schedule',
  'send',
  'settle',
  'ship',
  'stop',
  'submit',
  'subscribe',
  'suppress',
  'sync',
  'toggle',
  'tokenize',
  'transfer',
  'translate',
]);

/** Build the shape a predicate reads. Pure, and safe to call in a test. */
export function createRouteContext(entry: CatalogEntry): RouteContext {
  const segments = entry.path === '/' ? [] : entry.path.split('/').filter(Boolean);
  const leaf = segments.at(-1) ?? '';
  return {
    entry,
    path: entry.path,
    domain: entry.domain,
    segments,
    leaf,
    depth: segments.length,
    hasParam: segments.some((segment) => /^\{.+\}$/.test(segment)),
    isStep: /^(?:step[-_]?\d+|\d+)$/i.test(leaf),
    isCommand: WRITE_LEAVES.has(leaf) || entry.method !== 'GET',
    isTool: entry.domain === 'hydroma' && segments[1] === 'tools',
  };
}

/*
 * The four matchers below return `boolean`, not a curried predicate.
 *
 * That is deliberate, and it is a correction. Written the other way round —
 * `at('/a', '/b')` returning a function — a matcher used by mistake as a value
 * inside a larger expression is a *function*, which is truthy, so the branch
 * passes and the template silently claims every route in that domain. It
 * type-checked, because a curried matcher genuinely is a `RoutePredicate`.
 * Returning a boolean makes that mistake a compile error instead, which is the
 * only thing between this file and another silent over-claim.
 */
const at = (context: RouteContext, ...paths: readonly string[]): boolean =>
  paths.includes(context.path);

const under = (context: RouteContext, ...prefixes: readonly string[]): boolean =>
  prefixes.some((prefix) => context.path === prefix || context.path.startsWith(`${prefix}/`));

const leafIs = (context: RouteContext, ...leaves: readonly string[]): boolean =>
  leaves.includes(context.leaf);

const domainIs = (context: RouteContext, ...domains: readonly CatalogDomain[]): boolean =>
  domains.includes(context.domain);

/* -------------------------------------------------------------------------- */
/*  Labels                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * The labels a template renders, all of them supplied.
 *
 * `apps/web/messages/**` is not owned by this module, and a component library
 * that carries its own strings cannot be translated — the defect the 53 public
 * pages had. So every visible string arrives here, already resolved through
 * `getTranslations` — `StateLabels` is the same five-state copy
 * `ResourcePage` builds today in `resourceLabels()`, so no new namespace is
 * needed for the states. The keys a template needs beyond those are listed in
 * `REQUIRED_LABEL_KEYS` so the missing ones can be added in one pass.
 */
export interface TemplateLabels extends StateLabels {
  /** Heading for each region the template renders. Absent → no heading. */
  regions: Partial<Record<RequiredRegion, string>>;
  /** Accessible name for the provenance stamp. */
  provenance: string;
  /** Copy for the live/unavailable badge. */
  live: string;
  unavailable: string;
  /** Label of the primary action, when the template has one. */
  primaryAction?: string;
  /** Trailing attribution line, e.g. the catalogue slug. */
  footer?: string;
}

/**
 * The render-prop contract `ResourcePage` already offers, reused verbatim:
 * `children` may be a node or a function of `{ total, state, path }`, and
 * `state` is the same `DataState` the renderer already computes. Inventing a
 * parallel contract here would mean two answers to "what is this page showing".
 */
export interface TemplateRenderContext {
  total: number;
  state: DataState;
  path: string;
}

export type TemplateChildren = ReactNode | ((context: TemplateRenderContext) => ReactNode);

/** Resolves the `TemplateChildren` union. Shared by every template component. */
export function renderTemplateChildren(
  children: TemplateChildren | undefined,
  context: TemplateRenderContext,
): ReactNode {
  return typeof children === 'function' ? children(context) : (children ?? null);
}

/* -------------------------------------------------------------------------- */
/*  The template contract                                                     */
/* -------------------------------------------------------------------------- */

export interface PageTemplate {
  readonly id: TemplateId;
  /** Plan code, §4.4. */
  readonly plan: PlanCode;
  /** Plan name in English, for code, logs and reports. */
  readonly name: string;
  /** Plan name as written in §4.4, so a note can quote it. */
  readonly planName: string;
  /** Where the plan defines it, e.g. `§4.4 · §6.3`. */
  readonly planSection: string;
  /** One sentence: what a reader can do here that they cannot on the sibling. */
  readonly intent: string;
  readonly density: PageDensity;
  /** Regions in render order. `provenance` is enforced separately, below. */
  readonly regions: readonly RequiredRegion[];
  readonly provenance: ProvenanceRequirement;
  /** Exactly the five states of §4.5. */
  readonly states: PageStateCoverage;
  /** `null` on a surface that is read-only by design. */
  readonly primaryAction: PrimaryAction | null;
  /** Every surface this template claims, in plain language. Reported by tests. */
  readonly surfaces: readonly string[];
  /** Claims a catalogue entry. Partitions the catalogue; see `matchTemplates`. */
  readonly matches: RoutePredicate;
}

/* -------------------------------------------------------------------------- */
/*  The twelve                                                                */
/* -------------------------------------------------------------------------- */

/** Science pages that are registers of other things, not documents. */
const SCIENCE_REGISTERS = ['case-studies', 'data-sources', 'evidence-base', 'peer-review'];

/** Education pages that are a guide, not a browsable index. */
const EDUCATION_GUIDES = ['glossary', 'video-player'];

/** Marketplace leaves that open a commit form rather than a record. */
const VILLAGE_COMMANDS = ['register', 'interest', 'engaged'];

const T01: PageTemplate = {
  id: 'cover',
  plan: 'T01',
  name: 'Cover',
  planName: 'کاور',
  planSection: '§4.4 · §6.0',
  intent:
    'One full-bleed narrative surface: language choice, two actions and three stamped status lines.',
  density: 'comfortable',
  regions: ['title', 'status', 'provenance', 'state', 'data', 'actions', 'footer'],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'navigate',
    purpose: 'enter the public or the marketplace tree',
  },
  surfaces: ['the site root, which is a decision surface rather than a list'],
  matches: (context) => at(context, '/'),
};

const T02: PageTemplate = {
  id: 'narrative',
  plan: 'T02',
  name: 'Narrative',
  planName: 'محتوایی',
  planSection: '§4.4 · §6.1',
  intent:
    'A 72ch reading column with an edge table of contents. Nothing to do here but read and print.',
  density: 'comfortable',
  regions: ['title', 'status', 'provenance', 'state', 'data', 'detail', 'notes', 'print', 'footer'],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: null,
  surfaces: [
    'public introductions, audiences, goals and services',
    'evidence and methodology documents',
    'the AI policy pages and the about/platform pages',
    'developer and chain-parameter reference prose',
    'reference tables published as documents: crop calendar, crop parameters, soil regions',
  ],
  matches: (context) => {
    // `/help` is catalogued under the system context, so the help hub is
    // reached before the context switch rather than inside it.
    if (at(context, '/help')) return true;
    if (context.domain !== 'public') {
      return (
        domainIs(context, 'hydroma', 'learning') &&
        at(
          context,
          '/hydroma/carbon/verra/standards',
          '/learn/manual/crop-calendar',
          '/learn/manual/crop-params',
          '/learn/manual/soil-regions',
        )
      );
    }
    return (
      at(
        context,
        '/about',
        '/design-system',
        '/evidence',
        '/help/personas',
        '/home',
        '/platform',
        '/prototype',
        '/public/channels',
        '/public/cta',
        '/public/home',
        '/public/why',
        '/services',
        '/validation',
        '/ai',
        '/ai/ethics',
        '/ai/limits',
        '/developers',
        '/trust',
        '/trust/blockchain/info',
      ) ||
      under(context, '/public/goals', '/public/services') ||
      // The science pages are documents, except the four that are registers of
      // other things; §6.1 puts a register on T03, not in a reading column.
      (under(context, '/public/science') && !leafIs(context, ...SCIENCE_REGISTERS))
    );
  },
};

const T03: PageTemplate = {
  id: 'discovery',
  plan: 'T03',
  name: 'Discovery',
  planName: 'کشف/فهرست',
  planSection: '§4.4 · §6.1 · §6.2',
  intent:
    'A sticky filter header over a heterogeneous result grid, with a result count the reader can trust.',
  density: 'compact',
  regions: [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'actions',
    'notes',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: { region: 'actions', kind: 'filter', purpose: 'narrow the result set' },
  surfaces: [
    'marketplace categories, products, vendors, marketplaces, villages and bazaars',
    'marketplace search in all its forms, including the unresolved catch-all',
    'learning libraries, courses, workshops and the content index',
    'scientific references, model registries and the platform component gallery',
    'public audiences, SDKs, cookbooks and partners as browsable sets',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'marketplace':
        return (
          at(
            context,
            '/market',
            '/market/bazaars',
            '/market/compare',
            '/market/marketplaces',
            '/market/producers',
            '/market/products',
            '/market/products/search',
            '/market/vendors',
            '/market/bazaars/{id}/stores',
            // The unresolved marketplace catch-all. An unknown `/market/x` is a
            // browsing surface today (`MarketplaceTemplatePage` renders it), so
            // it inherits T03 rather than T11. Recorded in the wiring notes.
            '/market/{*segments}',
          ) ||
          under(context, '/market/categories', '/market/search') ||
          // Villages: the record is T04, the recommender is T07, the commit
          // leaves are T05, and everything else is a list to browse.
          (under(context, '/market/villages') &&
            context.path !== '/market/villages/{village_id}' &&
            !leafIs(
              context,
              ...VILLAGE_COMMANDS,
              'ai-recommendations',
              // Three village routes are `POST` in the catalogue because the
              // reader posts a demand, an engagement or a festival, so they are
              // commit screens rather than browsable lists.
              'demands',
              'engagements',
              'festivals',
            )) ||
          (under(context, '/market/marketplaces/{marketplace_id}') && leafIs(context, 'shops')) ||
          (under(context, '/market/vendors/{vendor_id}') && leafIs(context, 'orders', 'products'))
        );
      case 'public':
        return (
          at(
            context,
            '/ai/agents',
            '/ai/glossary',
            '/references',
            '/scientific-models',
            '/developers/cookbooks',
            '/developers/partners',
            '/developers/sdks',
            '/trust/audits',
            '/trust/carbon-registry',
            '/trust/provenance',
            '/trust/blockchain/ecosystem-fund/grant',
            '/trust/blockchain/impact/certificate',
            '/trust/blockchain/treasury/proposal',
          ) ||
          under(context, '/public/components', '/public/audiences') ||
          (under(context, '/public/science') && leafIs(context, ...SCIENCE_REGISTERS))
        );
      case 'hydroma':
        return at(
          context,
          '/hydroma/carbon',
          '/hydroma/climate',
          '/hydroma/economics',
          '/hydroma/farms',
          '/hydroma/carbon/verra/search',
          // The five `_SPECS` families. Each index page lists the same
          // `{count, models}` envelope as the three generated ones above, so
          // they are registers of other things and not documents, which is what
          // puts them on T03 rather than T02.
          '/hydroma/indices',
          '/hydroma/mrv',
          '/hydroma/simulation',
          '/hydroma/soil',
          '/hydroma/water',
          '/hydroma/models',
          // The verification suite is one register read at three depths: the
          // roll-up, the catalogue of checks, and the published values they are
          // judged against. `run` is not here — it invokes a check and reads the
          // value it produced, which is the instrument T07 already owns for
          // `/hydroma/{carbon,climate,economics}/{model_id}/run`.
          '/hydroma/validation',
          '/hydroma/validation/checks',
          '/hydroma/validation/reference-data',
        );
      case 'research':
        return (
          at(
            context,
            '/research/science/agrovoc',
            '/research/science/citations',
            '/research/science/citations/index',
            '/research/science/datasets',
            '/research/science/model-cards',
          ) ||
          (under(context, '/research/hub') && !context.isCommand)
        );
      case 'learning':
        return (
          at(
            context,
            '/learn/content/search',
            '/learn/legal',
            '/learn/legal/locales',
            '/learn/legal/slugs',
            '/learn/manual/sites',
          ) ||
          (under(context, '/public/education') && !leafIs(context, ...EDUCATION_GUIDES))
        );
      default:
        return false;
    }
  },
};

const T04: PageTemplate = {
  id: 'detail',
  plan: 'T04',
  name: 'Detail',
  planName: 'جزئیات',
  planSection: '§4.4 · §6.2 · §6.3',
  intent:
    'One entity: a main column for its facts and a sticky action column, with document and history tabs beneath.',
  density: 'comfortable',
  regions: [
    'title',
    'status',
    'provenance',
    'state',
    'data',
    'actions',
    'summary',
    'detail',
    'notes',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'summary', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: { region: 'actions', kind: 'submit', purpose: 'act on this one entity' },
  surfaces: [
    'marketplace product, bazaar, store, vendor, marketplace, village, order and payment records',
    'scientific model, registry, credit and site records',
    'device records and their readings',
    'account, profile and subscription records',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'marketplace':
        return (
          (under(context, '/market/product/{id}', '/market/products/{product_id}') &&
            !context.isCommand) ||
          (under(context, '/market/payments/{payment_id}') && !context.isCommand) ||
          at(
            context,
            '/market/bazaars/{id}',
            '/market/bazaars/{id}/map',
            '/market/escrow/{id}',
            '/market/marketplaces/{marketplace_id}',
            '/market/orders/{id}/dispute',
            '/market/orders/{id}/evidence',
            '/market/orders/{id}/timeline',
            '/market/orders/{id}/tracking',
            // The order itself, and the states the state machine currently
            // allows it to move to. `run` is not here — a transition the gateway
            // refuses returns an error, so this surface offers no command and is
            // a read of the record, not a commit.
            '/market/orders/{id}',
            '/market/orders/{id}/transitions',
            '/market/orders/{order_id}/track',
            '/market/stores/{id}',
            '/market/vendors/{vendor_id}',
            '/market/villages/{village_id}',
            '/market/wallet',
          )
        );
      case 'hydroma':
        return (
          (under(
            context,
            '/hydroma/carbon',
            '/hydroma/climate',
            '/hydroma/economics',
            // The five `_SPECS` families, whose detail pages carry the same
            // parameter contract as the three generated ones.
            '/hydroma/indices',
            '/hydroma/mrv',
            '/hydroma/simulation',
            '/hydroma/soil',
            '/hydroma/water',
            // One model's registry record and one model's validation report.
            // `run` is excluded by the same test that keeps a run off
            // `/hydroma/carbon/{model_id}`: a run is something you commit.
            '/hydroma/models',
          ) &&
            context.hasParam &&
            // A run is something you commit, and a credit history is a report.
            !leafIs(context, 'run', 'history')) ||
          at(
            context,
            '/hydroma/carbon/credits/{token_id}/verify',
            '/hydroma/carbon/verra/{registry_id}',
            '/hydroma/elevation/grid/{site_id}',
          )
        );
      case 'public':
        return at(
          context,
          '/trust/blockchain/ecocoin/wallet/{user_id}',
          '/trust/blockchain/ecosystem-fund/grant/{grant_id}/milestone',
          '/trust/blockchain/oracle/attestation',
          '/trust/blockchain/oracle/challenge/{activity_id}',
        );
      case 'system':
        return under(context, '/system/iot/devices/{device_id}') && !context.isCommand;
      case 'workspace':
        return at(
          context,
          '/workspace/commerce/orders/{order_id}',
          '/workspace/disputes/{dispute_id}',
          '/workspace/finance/ledger/accounts/{account_id}/balance',
          '/workspace/finance/wallet',
        );
      case 'inclusive':
        return at(
          context,
          '/auth/2fa/methods',
          '/auth/2fa/status',
          '/auth/account/status',
          '/auth/achievements',
          '/auth/assets',
          '/auth/billing/subscription',
          '/auth/me',
          '/auth/oauth/connections',
          '/auth/preferences/extended',
          '/auth/profile/public',
        );
      case 'learning':
        return (
          at(context, '/learn/certificate-verify') ||
          under(
            context,
            '/learn/manual/sites/{site_id}',
            '/learn/manual/climate-normals/{site_id}',
            '/learn/manual/weather-daily/{site_id}',
          )
        );
      default:
        return false;
    }
  },
};

const T05: PageTemplate = {
  id: 'flow',
  plan: 'T05',
  name: 'Multi-step flow',
  planName: 'جریان چندمرحلهای',
  planSection: '§4.4 · §6.2',
  intent:
    'A linear stepper with a per-step save and a standing summary of what committing will do.',
  density: 'comfortable',
  regions: [
    'title',
    'status',
    'provenance',
    'navigation',
    'state',
    'data',
    'actions',
    'summary',
    'detail',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'summary', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'submit',
    purpose: 'commit this step and continue',
  },
  surfaces: [
    'cart and the whole checkout tree, including the versioned contract step',
    'bazaar and store creation wizards',
    'account sign-in, sign-up, password, e-mail, profile and two-factor journeys',
    'marketplace, wallet, order, credit, chain and carbon commands',
    'enrolment, assessment, newsletter, pilot-application and visit-request forms',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'marketplace':
        return (
          under(
            context,
            '/market/cart',
            '/market/checkout',
            '/market/bazaars/{id}/wizard',
            '/market/stores/create',
          ) ||
          at(context, '/market/bazaars/create', '/market/bazaars/{id}/settings') ||
          at(context, '/market/marketplaces/{marketplace_id}/members') ||
          (under(
            context,
            '/market/bazaars',
            '/market/orders',
            '/market/payments',
            '/market/product/{id}',
            '/market/products/{product_id}',
            '/market/villages',
          ) &&
            context.isCommand &&
            // The recommender is a POST that renders a model, so it is T07 and
            // not a commit form. Naming it here is what keeps the two apart.
            !leafIs(context, 'ai-recommendations'))
        );
      case 'hydroma':
        return at(
          context,
          '/hydroma/carbon/credits/retire',
          '/hydroma/carbon/credits/transfer',
          '/hydroma/carbon/tokenize',
          '/hydroma/carbon/verra/sync',
        );
      case 'inclusive':
        return (
          at(context, '/auth/account/bio') ||
          under(context, '/auth/api-keys/{key_id}') ||
          at(
            context,
            '/account/session',
            '/auth/2fa/toggle',
            '/auth/change-password',
            '/auth/deactivate',
            '/auth/email/change-confirm',
            '/auth/email/change-request',
            '/auth/export-data',
            '/auth/forgot-password',
            '/auth/login',
            '/auth/oauth/connect',
            '/auth/oauth/disconnect/{provider}',
            '/auth/preferences',
            '/auth/profile',
            '/auth/signup',
          )
        );
      case 'public':
        return (
          at(
            context,
            '/ai/feedback',
            '/help/chat',
            '/help/contact',
            '/public/visit',
            '/public/visit-request-submit',
          ) ||
          under(context, '/public/pilot/apply') ||
          // Chain commands: a grant approval, a phase activation, a token
          // movement. Each is a commit screen, so T05 and not a record.
          under(context, '/trust/blockchain/phasegate/activate') ||
          (under(context, '/trust/blockchain') &&
            leafIs(context, 'approve', 'distribute', 'earn', 'redeem', 'transfer'))
        );
      case 'system':
        return (
          at(context, '/system/dashboard/refresh-data') ||
          (under(context, '/system/iot/devices/{device_id}') && context.isCommand)
        );
      case 'workspace':
        return (
          under(context, '/workspace/settings') ||
          (under(context, '/workspace/commerce', '/workspace/disputes') && context.isCommand) ||
          at(
            context,
            '/workspace/finance/ledger/batch',
            '/workspace/finance/ledger/batch/{batch_id}/post',
            '/workspace/finance/payments/intent',
            '/workspace/finance/wallet/earn',
            '/workspace/finance/wallet/redeem',
          )
        );
      case 'research':
        return context.isCommand;
      case 'learning':
        return at(
          context,
          '/learn/assessment-submission',
          '/learn/course-enrolment',
          '/learn/library-checkout',
          '/learn/newsletter/subscribe',
        );
      default:
        return false;
    }
  },
};

const T06: PageTemplate = {
  id: 'dashboard',
  plan: 'T06',
  name: 'Dashboard',
  planName: 'داشبورد',
  planSection: '§4.4 · §6.2 · §6.3',
  intent:
    'A row of indicators, a grid of widgets the reader can rearrange, and a timeline underneath.',
  density: 'compact',
  regions: [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'summary',
    'detail',
    'notes',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'summary', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'navigate',
    purpose: 'drill into the thing being watched',
  },
  surfaces: [
    'the HyDroMa hub, its storage counters and the credit balance',
    'system dashboards and analytics, public and internal',
    'marketplace statistics, order history, bazaar analytics and payouts',
    'chain counters, balances and oracle metrics',
    'personal feeds and workspace overview, targets and knowledge',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'hydroma':
        return at(
          context,
          '/hydroma',
          '/hydroma/db-stats',
          '/hydroma/carbon/credits/balance',
          // How many models the registry declares and how each one describes its
          // own validation state: counts across the catalogue, which is what T06
          // is for, as against the suite's per-check rows on T03.
          '/hydroma/slaughterhouse/status',
        );
      case 'system':
        return (
          under(context, '/system/dashboard/public', '/system/analytics') ||
          at(context, '/system/dashboard/data', '/system/incident-timeline')
        );
      case 'marketplace':
        return (
          at(
            context,
            '/market/bazaar-analytics',
            '/market/bazaars/{id}/analytics',
            '/market/bazaars/{id}/supervision',
            '/market/stats',
            '/market/vendor-payouts',
          ) ||
          (at(context, '/market/orders') && !context.isCommand) ||
          // The same session-scoped order list narrowed to the held-against-
          // escrow subset. It was being captured by `/market/escrow/{id}`, which
          // returned a payment record for a payment whose id was the literal
          // string `orders`.
          at(context, '/market/escrow/orders')
        );
      case 'workspace':
        return at(
          context,
          '/workspace',
          '/workspace/knowledge',
          '/workspace/overview',
          '/workspace/target-progress',
          '/workspace/targets',
        );
      case 'research':
        return at(context, '/research');
      case 'inclusive':
        return at(context, '/auth/activity/history', '/auth/notifications');
      case 'learning':
        return at(context, '/learn/video-progress');
      case 'public':
        return (
          at(context, '/public/model-count', '/public/pilot/stats') ||
          under(context, '/trust/blockchain/oracle/metrics') ||
          (under(context, '/trust/blockchain') && leafIs(context, 'stats', 'balance'))
        );
      default:
        return false;
    }
  },
};

const T07: PageTemplate = {
  id: 'instrument',
  plan: 'T07',
  name: 'Scientific instrument',
  planName: 'ابزار علمی',
  planSection: '§4.4 · §6.3',
  intent:
    'A sticky input panel beside an output scene, under a bar that always shows model version, calibration and confidence interval.',
  density: 'dense',
  regions: [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'actions',
    'summary',
    'detail',
    'notes',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'summary', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'run',
    purpose: 're-run with the same inputs so a result can be reproduced',
  },
  surfaces: [
    'the 62 HyDroMa tools and their execute endpoints',
    'the six named analyses',
    'model run endpoints for carbon, climate and economics',
    'the AI assistant, chat, analysis, voice and stream surfaces',
    'the research workbench, the experiments, the farm recommender and the developer playground',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'hydroma':
        return (
          context.isTool ||
          under(context, '/hydroma/analyses') ||
          at(
            context,
            '/hydroma/carbon/{model_id}/run',
            '/hydroma/climate/{model_id}/run',
            '/hydroma/economics/{model_id}/run',
            '/hydroma/elevation/erosion-effect/{site_id}',
            // A verification check is invoked and read, the same shape as a
            // model run: parameters in, one value out, judged against a
            // tolerance the contract states.
            '/hydroma/validation/run',
          )
        );
      case 'public':
        return (
          under(context, '/ai/analysis') ||
          at(
            context,
            '/ai/assistant',
            '/ai/chat',
            '/ai/history',
            '/ai/stream',
            '/ai/voice',
            '/ai/voice/tts',
            '/developers/playground',
          )
        );
      case 'research':
        return (
          under(context, '/research/experiments') ||
          at(context, '/research/workspace/{experimentId}')
        );
      case 'marketplace':
        return at(context, '/market/villages/{village_id}/ai-recommendations');
      case 'system':
        return at(context, '/system/dashboard/recommendations/{farm_id}');
      default:
        return false;
    }
  },
};

const T08: PageTemplate = {
  id: 'ledger',
  plan: 'T08',
  name: 'Management table',
  planName: 'جدول مدیریت',
  planSection: '§4.4 · §6.2 · §6.4',
  intent:
    'Advanced filters over a dense grid with a detail drawer and bulk selection. Built to be scanned, not read.',
  density: 'dense',
  regions: [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'actions',
    'detail',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'export',
    purpose: 'act on a selected set of rows',
  },
  surfaces: [
    'the entire admin context, as §6.4 states outright',
    'workspace operations, commerce, disputes and the finance ledger',
    'marketplace administration, approval queues, finance, governance and arbitration',
    'developer changelog and webhooks, and account API keys',
    'system device, automation, migration and queue inspection',
  ],
  matches: (context) => {
    switch (context.domain) {
      // §6.4 is unambiguous: every admin page is T08, with a command rail and
      // a hedger. Forty routes, one archetype, no exceptions to maintain.
      case 'admin':
        return true;
      case 'workspace':
        return (
          at(
            context,
            '/workspace/approvals',
            '/workspace/assignments',
            '/workspace/audit',
            '/workspace/cases',
            '/workspace/finance/accounts',
            '/workspace/finance/idempotency/keys',
            '/workspace/finance/ledger/entries',
            '/workspace/operations',
            '/workspace/operations/events',
            '/workspace/operations/jobs',
            '/workspace/team',
          ) ||
          (under(context, '/workspace/commerce', '/workspace/disputes') &&
            !context.isCommand &&
            // The single-record leaves are T04; the grid is everything else.
            !leafIs(context, '{order_id}', '{dispute_id}'))
        );
      case 'marketplace':
        return (
          under(context, '/market/admin') ||
          at(
            context,
            '/market/bazaars/{id}/disputes',
            '/market/bazaars/{id}/finances',
            '/market/bazaars/{id}/governance',
            '/market/escrow-dispute-arbitration',
            '/market/marketplaces/{marketplace_id}/approve',
          )
        );
      case 'system':
        return at(
          context,
          '/system/automation/agent-run',
          '/system/iot/devices',
          '/system/iot/devices/provision-qr',
          '/system/migration-runner',
          '/system/queue-inspector',
        );
      case 'public':
        return at(context, '/developers/changelog', '/developers/webhooks');
      case 'inclusive':
        return at(context, '/auth/api-keys');
      default:
        return false;
    }
  },
};

const T09: PageTemplate = {
  id: 'legal',
  plan: 'T09',
  name: 'Legal document',
  planName: 'سند حقوقی',
  planSection: '§4.4 · §6.1',
  intent:
    'Numbered clauses, a visible version and a diff against the previous one, with acceptance recorded.',
  density: 'comfortable',
  regions: ['title', 'status', 'provenance', 'state', 'data', 'detail', 'print', 'notes', 'footer'],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: null,
  surfaces: [
    'the public policy set: privacy, terms, cookies, governance, licensing, accessibility',
    'versioned legal texts published through the learning service',
    'statements, disclosure and sanctions policy',
  ],
  matches: (context) => {
    if (context.domain === 'public') {
      return (
        at(context, '/legal', '/statements', '/trust/disclosure', '/trust/sanctions') ||
        under(context, '/public/policy')
      );
    }
    if (context.domain === 'inclusive') return at(context, '/accessibility');
    return domainIs(context, 'learning') && under(context, '/learn/legal/{locale}');
  },
};

const T10: PageTemplate = {
  id: 'report',
  plan: 'T10',
  name: 'Report / print',
  planName: 'گزارش/چاپ',
  planSection: '§4.4 · §6.3',
  intent:
    'A document with its own print stylesheet, a server-side PDF, and the period stated on the page itself.',
  density: 'compact',
  regions: [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'summary',
    'detail',
    'print',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: { region: 'actions', kind: 'print', purpose: 'produce the document' },
  surfaces: [
    'invoices and the annual transparency report',
    'workspace profit and loss, trial balance and reconciliation',
    'impact certificates, the oracle report and credit movement history',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'marketplace':
        return at(context, '/market/order-invoice');
      case 'workspace':
        return at(
          context,
          '/workspace/finance/ledger/profit-and-loss',
          '/workspace/finance/ledger/trial-balance',
          '/workspace/finance/reconciliation/full',
          '/workspace/finance/reconciliation/wallet-ledger',
          '/workspace/report-export',
          '/workspace/reports',
        );
      case 'hydroma':
        return at(context, '/hydroma/carbon/credits/{token_id}/history');
      case 'public':
        return (
          at(context, '/trust/report', '/trust/blockchain/oracle/report') ||
          (under(context, '/trust/blockchain/impact/certificate') && context.hasParam)
        );
      default:
        return false;
    }
  },
};

const T11: PageTemplate = {
  id: 'system',
  plan: 'T11',
  name: 'System',
  planName: 'سامانه‌ها',
  planSection: '§4.4 · §6.6',
  intent:
    'One calm column that says what is wrong, what still works, and how to get back. No decoration.',
  density: 'comfortable',
  regions: ['title', 'status', 'provenance', 'state', 'data', 'actions', 'notes', 'footer'],
  provenance: { region: 'provenance', anchor: 'data', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'navigate',
    purpose: 'get the reader back to a working surface',
  },
  surfaces: [
    'status, service health, offline and client-update surfaces',
    'AI and chain health reads, the manual and Zenodo status reads',
    'rate limiting, legacy compatibility and the web-payment callback receiver',
  ],
  matches: (context) => {
    switch (context.domain) {
      case 'system':
        return at(
          context,
          '/status',
          '/system',
          '/system/automation/health',
          '/system/locale-fallback',
          '/system/pwa-update',
          '/system/webgpu-fallback',
        );
      case 'inclusive':
        return at(
          context,
          '/auth/legacy',
          '/auth/logout',
          '/auth/rate-limit',
          '/offline',
          '/simple',
        );
      case 'public':
        return (
          at(context, '/ai/health', '/developers/status-api') ||
          (under(context, '/trust/blockchain') && leafIs(context, 'health', 'status'))
        );
      case 'research':
        return at(context, '/research/science/zenodo/status');
      case 'learning':
        return at(context, '/learn/manual/status');
      case 'workspace':
        return under(context, '/workspace/finance/payments/webhook');
      default:
        return false;
    }
  },
};

const T12: PageTemplate = {
  id: 'learning',
  plan: 'T12',
  name: 'Learning',
  planName: 'آموزشی',
  planSection: '§4.4 · §6.1 · §6.6',
  intent:
    'Two columns of step-by-step guidance with the media beside it and the vocabulary underneath.',
  density: 'comfortable',
  regions: [
    'title',
    'status',
    'provenance',
    'navigation',
    'state',
    'data',
    'detail',
    'notes',
    'footer',
  ],
  provenance: { region: 'provenance', anchor: 'detail', required: true },
  states: ['loading', 'empty', 'error', 'partial', 'offline'],
  primaryAction: {
    region: 'actions',
    kind: 'navigate',
    purpose: 'go to the next step of the guide',
  },
  surfaces: [
    'the learning hub, the video caption pack and the video player',
    'the bilingual glossary',
    'the telecom hub and the USSD, SMS and voice channel records',
  ],
  matches: (context) => {
    if (context.domain === 'learning') {
      return at(
        context,
        '/learn',
        '/learn/video-caption-pack',
        '/public/education/glossary',
        '/public/education/video-player',
      );
    }
    return (
      domainIs(context, 'inclusive') && (at(context, '/telecom') || under(context, '/inclusive'))
    );
  },
};

/**
 * The twelve, in plan order.
 *
 * `satisfies` rather than `: PageTemplate[]` so a thirteenth template is a
 * visible edit here and a deletion is a visible edit here. The length is
 * asserted in the colocated test as well, so removing one fails the suite.
 */
export const PAGE_TEMPLATES = [
  T01,
  T02,
  T03,
  T04,
  T05,
  T06,
  T07,
  T08,
  T09,
  T10,
  T11,
  T12,
] as const satisfies readonly PageTemplate[];

export const PAGE_TEMPLATE_COUNT = 12;

export const TEMPLATE_BY_ID: Readonly<Record<TemplateId, PageTemplate>> = Object.fromEntries(
  PAGE_TEMPLATES.map((template) => [template.id, template]),
) as Record<TemplateId, PageTemplate>;

/* -------------------------------------------------------------------------- */
/*  Resolution                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Every template that claims a route.
 *
 * Returning *all* matches rather than the first one is deliberate: the point of
 * the gate is that this list holds exactly one element for each of the 600
 * catalogue entries. A first-match-wins resolver would hide an overlap behind an
 * ordering accident, and an ordering accident is what put 110 scientific pages
 * on one layout in the first place.
 */
export function matchTemplates(context: RouteContext): readonly PageTemplate[] {
  return PAGE_TEMPLATES.filter((template) => template.matches(context));
}

/** The template for a route, or `null` when no template claims it. */
export function templateForEntry(entry: CatalogEntry): PageTemplate | null {
  const matched = matchTemplates(createRouteContext(entry));
  return matched.length === 1 ? matched[0] : null;
}

/**
 * The template for a route, or an error that names the route.
 *
 * The generator calls this, so an unrouted path fails the build with the path in
 * the message rather than rendering a page with no designed layout.
 */
export function requireTemplateForEntry(entry: CatalogEntry): PageTemplate {
  const context = createRouteContext(entry);
  const matched = matchTemplates(context);
  if (matched.length === 1) return matched[0];
  if (matched.length === 0) {
    throw new Error(
      `no page template claims "${entry.path}" (${entry.domain}). ` +
        'Assign it a T01-T12 archetype, or extend the template that owns its context.',
    );
  }
  throw new Error(
    `"${entry.path}" (${entry.domain}) is claimed by more than one page template: ` +
      `${matched.map((template) => `${template.plan}/${template.id}`).join(', ')}. ` +
      'Exactly one archetype per route, or the layout is decided by declaration order.',
  );
}

export interface TemplateCoverage {
  readonly counts: Readonly<Record<TemplateId, number>>;
  /** Routes no template claims. */
  readonly unmatched: readonly string[];
  /** Routes more than one template claims, with the claimants. */
  readonly ambiguous: readonly { path: string; templates: readonly string[] }[];
}

/**
 * Runs the partition over a set of catalogue entries.
 *
 * The colocated test asserts `unmatched` and `ambiguous` are both empty and
 * reports `counts`; `scripts/check-page-templates.mjs` asserts the same over the
 * real catalogue so the gate runs without a test runner.
 */
export function templateCoverage(entries: readonly CatalogEntry[]): TemplateCoverage {
  const counts = Object.fromEntries(TEMPLATE_IDS.map((id) => [id, 0])) as Record<
    TemplateId,
    number
  >;
  const unmatched: string[] = [];
  const ambiguous: { path: string; templates: string[] }[] = [];

  for (const entry of entries) {
    const matched = matchTemplates(createRouteContext(entry));
    if (matched.length === 0) {
      unmatched.push(`${entry.path} (${entry.domain})`);
      continue;
    }
    if (matched.length > 1) {
      ambiguous.push({
        path: entry.path,
        templates: matched.map((template) => `${template.plan}/${template.id}`),
      });
      continue;
    }
    counts[matched[0].id] += 1;
  }

  return { counts, unmatched, ambiguous };
}

/* -------------------------------------------------------------------------- */
/*  Strings the templates need                                                */
/* -------------------------------------------------------------------------- */

/**
 * The message keys a template asks its caller for, by namespace.
 *
 * `messages/en.json` is not owned by this module. Rather than hard-code English
 * into a layout, the templates declare what they need here, so the catalogue and
 * messages owner can add the namespace in one pass instead of discovering a
 * missing key from a rendered page.
 */
export const REQUIRED_LABEL_KEYS = {
  /** Per-region headings, one per `RequiredRegion` a template can render. */
  'templates.regions': [
    'title',
    'status',
    'provenance',
    'filters',
    'state',
    'data',
    'actions',
    'summary',
    'detail',
    'notes',
    'print',
    'footer',
    'navigation',
  ],
  /** The five states of §4.5, plus the retry affordance. */
  'templates.states': ['loading', 'empty', 'error', 'partial', 'offline', 'retry'],
  /** Live / unavailable badge, reusing the existing `statusLine` copy. */
  'templates.status': ['live', 'unavailable'],
  /** One primary-action label per `PrimaryActionKind`. */
  'templates.actions': ['navigate', 'submit', 'run', 'retry', 'filter', 'print', 'export'],
  /** Provenance popover, reusing `ProvenanceStamp`'s existing labels. */
  'templates.provenance': ['heading', 'source', 'observedAt', 'verified', 'unverified'],
  /** Trailing attribution, e.g. the catalogue slug. */
  'templates.footer': ['attribution'],
} as const satisfies Readonly<Record<string, readonly string[]>>;
