import { describe, expect, it } from 'vitest';
import {
  getMarketplaceRouteGroup,
  MARKETPLACE_ROUTE_GROUPS,
  marketplaceRoutePlanTotal,
} from './marketplace-routes';

describe('marketplace route plan', () => {
  it('covers the planned 444 route surfaces', () => {
    expect(marketplaceRoutePlanTotal).toBe(444);
    expect(MARKETPLACE_ROUTE_GROUPS).toHaveLength(15);
  });

  it('has unique group ids, bases and prefixes', () => {
    const ids = new Set(MARKETPLACE_ROUTE_GROUPS.map((group) => group.id));
    const bases = new Set(MARKETPLACE_ROUTE_GROUPS.map((group) => group.base));
    const routePrefixes = new Set(
      MARKETPLACE_ROUTE_GROUPS.map((group) => `${group.base}/${group.prefix}`),
    );

    expect(ids.size).toBe(MARKETPLACE_ROUTE_GROUPS.length);
    expect(bases.size).toBe(MARKETPLACE_ROUTE_GROUPS.length);
    expect(routePrefixes.size).toBe(MARKETPLACE_ROUTE_GROUPS.length);
  });

  it('exposes group lookup for route generation', () => {
    expect(getMarketplaceRouteGroup('purchase')?.count).toBe(26);
    expect(getMarketplaceRouteGroup('purchase')?.id).toBe('purchase');
    expect(getMarketplaceRouteGroup('unknown')).toBeUndefined();
  });
});
