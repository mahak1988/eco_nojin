import { MARKETPLACE_ROUTE_GROUPS } from '@/lib/marketplace-routes';

/**
 * The marketplace surfaces the `market/[...segments]` catch-all is allowed to
 * answer.
 *
 * Why this table exists
 * ---------------------
 * The catch-all used to resolve a path by one rule only: a group base followed by
 * a `{prefix}-{index}` slug, and `notFound()` for everything else. That made the
 * file a 404 for every marketplace surface that is not one of the 444 generated
 * template slugs — a declared capability, a command endpoint, or a future
 * catalogue entry added after this file was written. A catch-all that refuses a
 * whole context is indistinguishable from a missing route to a reader and to a
 * crawler.
 *
 * So the rule is now a lookup. Each entry names the surface, whether a read
 * contract exists for it, and where its read side is. Nothing here is inferred
 * from the path: every `endpoint` is a path published by the running gateway's
 * OpenAPI document, and every entry corresponds to a `page-catalog.ts` row or to
 * a command the gateway mounts.
 *
 * The kinds
 * ---------
 *   - `unavailable` — a declared surface with no published read contract. It
 *     renders the shared honest template and stays `noindex`, which is what the
 *     MKT-G6 acceptance criterion requires of an unconnected capability.
 *   - `action` — a command endpoint. A `POST` is not a document, so this renders
 *     the command's identity, its read side and the reason no form is offered
 *     here. It never renders a form: a form would assert a workflow, a request
 *     body and a caller role that the contract does not describe, and the
 *     surfaces that *do* have a safe form are owned by their own page.
 *
 * The fallback group table
 * ------------------------
 * The 444 generated template slugs are unchanged and still `noindex`. They are
 * resolved last, so a declared surface above always wins over the generic
 * template, and an unrecognised path is still a 404 rather than a page that
 * invents itself.
 */

export type MarketplaceSurfaceKind = 'unavailable' | 'action';

export interface MarketplaceSurface {
  /** Declared marketplace path, with `{param}` where a segment is dynamic. */
  path: string;
  kind: MarketplaceSurfaceKind;
  /**
   * The published read contract for this surface, or `null` when the gateway
   * mounts only a command for it. Never a substitute, never a guess.
   */
  read: string | null;
  /**
   * HTTP method of the command. Present on `action` rows only; it is the reason
   * the row is not a page.
   */
  method?: 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  /** Repository file the declaration was read from. */
  sourceOfTruth: string;
}

const MARKETPLACE_ROUTER = 'services/api_gateway/routers/marketplace.py';
const VILLAGE_HUB_ROUTER = 'services/api_gateway/routers/village_hub.py';

/**
 * Read by the gateway, written by the catalogue owner: `apps/web/src/lib/domains/page-catalog.ts`
 * and `apps/web/src/lib/api/market.ts` declare these surfaces with `endpoint: null`,
 * so the template is the honest render.
 */
const DECLARED_UNAVAILABLE: MarketplaceSurface[] = [
  {
    path: '/market/bazaar-analytics',
    kind: 'unavailable',
    read: null,
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
  },
  {
    path: '/market/escrow-dispute-arbitration',
    kind: 'unavailable',
    read: null,
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
  },
  {
    path: '/market/order-invoice',
    kind: 'unavailable',
    read: null,
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
  },
  {
    path: '/market/vendor-payouts',
    kind: 'unavailable',
    read: null,
    sourceOfTruth: 'apps/web/src/lib/api/market.ts',
  },
];

/**
 * Command surfaces. Each is a mutation the gateway publishes, so each is a
 * declared marketplace path that the old catch-all refused.
 *
 * `read` names the endpoint a reader can actually be sent to for the same
 * subject. It is `null` where the gateway publishes no collection for the
 * command — for `POST /marketplaces/{id}/members` there is no
 * `GET /marketplaces/{id}/members`, and for `POST /villages/engagements` the
 * only reads are scoped to a parent opportunity or project — and the page says
 * so rather than linking to a route that does not exist.
 */
const DECLARED_ACTIONS: MarketplaceSurface[] = [
  {
    path: '/market/admin/products/{product_id}/approve',
    kind: 'action',
    method: 'PATCH',
    read: '/api/v1/marketplace/products/{product_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/admin/vendors/{vendor_id}/approve',
    kind: 'action',
    method: 'PATCH',
    read: '/api/v1/marketplace/vendors/{vendor_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/cart/{product_id}',
    kind: 'action',
    method: 'DELETE',
    read: '/api/v1/marketplace/cart',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/marketplaces',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/marketplaces',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/marketplaces/{marketplace_id}/approve',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/marketplaces/{marketplace_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/marketplaces/{marketplace_id}/members',
    kind: 'action',
    method: 'POST',
    read: null,
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/orders/{order_id}/complete',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/commerce/orders/{order_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/orders/{order_id}/confirm',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/orders/{order_id}/track',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/orders/{order_id}/dispute',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/disputes',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/orders/{order_id}/settle',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/commerce/orders/{order_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/payments',
    kind: 'action',
    method: 'POST',
    read: null,
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/payments/{payment_id}/confirm',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/payments/{payment_id}/escrow',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/payments/{payment_id}/escrow/refund',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/payments/{payment_id}/escrow',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/payments/{payment_id}/escrow/release',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/payments/{payment_id}/escrow',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/products/{product_id}/images',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/products/{product_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/products/{product_id}/tokenize',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/products/{product_id}',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/vendors',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/vendors',
    sourceOfTruth: MARKETPLACE_ROUTER,
  },
  {
    path: '/market/villages/engagements',
    kind: 'action',
    method: 'POST',
    read: null,
    sourceOfTruth: VILLAGE_HUB_ROUTER,
  },
  {
    path: '/market/villages/events/{event_id}/register',
    kind: 'action',
    method: 'POST',
    read: null,
    sourceOfTruth: VILLAGE_HUB_ROUTER,
  },
  {
    path: '/market/villages/festivals',
    kind: 'action',
    method: 'POST',
    read: null,
    sourceOfTruth: VILLAGE_HUB_ROUTER,
  },
  {
    path: '/market/villages/opportunities/{opportunity_id}/interest',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/villages/opportunities/{opportunity_id}/team',
    sourceOfTruth: VILLAGE_HUB_ROUTER,
  },
  {
    path: '/market/villages/{village_id}/ai-recommendations',
    kind: 'action',
    method: 'POST',
    read: '/api/v1/marketplace/villages/{village_id}',
    sourceOfTruth: VILLAGE_HUB_ROUTER,
  },
];

export const MARKETPLACE_SURFACES: readonly MarketplaceSurface[] = [
  ...DECLARED_UNAVAILABLE,
  ...DECLARED_ACTIONS,
];

/** Declared surfaces that resolve to a real read contract, for reporting. */
export const marketplaceSurfaceReadCount = MARKETPLACE_SURFACES.filter(
  (surface) => surface.read !== null,
).length;

/** `{ product_id: 'abc' }` for a matched surface, or `null` when it does not match. */
export function surfaceParams(
  surface: MarketplaceSurface,
  segments: string[],
): Record<string, string> | null {
  const pattern = surface.path.split('/').filter(Boolean).slice(1);
  if (pattern.length !== segments.length) return null;
  const params: Record<string, string> = {};
  for (const [index, segment] of pattern.entries()) {
    const value = segments[index];
    if (segment.startsWith('{')) {
      if (!value) return null;
      params[segment.slice(1, -1)] = value;
      continue;
    }
    if (segment !== value) return null;
  }
  return params;
}

/**
 * Resolve request segments against the declared surfaces.
 *
 * Exact paths are matched before patterns, so `/market/villages/festivals` can
 * never be shadowed by a `/market/villages/{village_id}/…` row that happens to
 * share a length, and a declared surface always wins over the generic template
 * fallback below it.
 */
export function resolveMarketplaceSurface(segments: string[]): MarketplaceSurface | null {
  const exact = MARKETPLACE_SURFACES.filter((surface) => !surface.path.includes('{'));
  const parameterised = MARKETPLACE_SURFACES.filter((surface) => surface.path.includes('{'));
  for (const surface of [...exact, ...parameterised]) {
    if (surfaceParams(surface, segments) !== null) return surface;
  }
  return null;
}

export interface MarketplaceGroupFallback {
  group: (typeof MARKETPLACE_ROUTE_GROUPS)[number];
  slug: string;
}

/**
 * The 444 generated template slugs, unchanged.
 *
 * A group base followed by `{prefix}-{index}`. Resolved after the declared
 * surfaces so it can never take a declared surface's route, and kept `noindex`
 * because none of the 444 has a published read contract.
 */
export function resolveMarketplaceGroup(segments: string[]): MarketplaceGroupFallback | null {
  const [base, slug] = segments;
  if (!slug) return null;
  const group = MARKETPLACE_ROUTE_GROUPS.find((candidate) => candidate.base === base);
  if (!group) return null;
  const prefix = `${group.prefix}-`;
  if (!slug.startsWith(prefix)) return null;
  const index = Number(slug.slice(prefix.length));
  if (!Number.isInteger(index) || index < 1 || index > group.count) return null;
  return { group, slug };
}

/**
 * Fill a path template's `{param}` placeholders from the matched surface.
 *
 * By name, not by position: the gateway path and the marketplace path have
 * different prefixes and different lengths, so positional substitution would put
 * a product id where a warehouse id belongs. Every `read` template above reuses
 * the surface's own parameter name, which is what makes the name lookup
 * sufficient — a template that renamed a parameter would be visible here as an
 * unsubstituted `{…}` rather than as a silently wrong request.
 */
export function fillPathParams(template: string, params: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_match, name: string) => {
    const value = params[name];
    return value === undefined ? '' : encodeURIComponent(value);
  });
}
