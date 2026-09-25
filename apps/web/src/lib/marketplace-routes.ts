export const MARKETPLACE_ROUTE_GROUPS = [
  { id: 'discovery', base: 'categories', prefix: 'discover', count: 30 },
  { id: 'search', base: 'search', prefix: 'global', count: 12 },
  { id: 'product', base: 'product', prefix: 'feature', count: 24 },
  { id: 'comparison', base: 'compare', prefix: 'view', count: 14 },
  { id: 'purchase', base: 'checkout', prefix: 'flow', count: 26 },
  { id: 'orders', base: 'orders', prefix: 'view', count: 24 },
  { id: 'trust', base: 'trust', prefix: 'record', count: 10 },
  { id: 'bazaars', base: 'bazaars', prefix: 'template', count: 42 },
  { id: 'stores', base: 'stores', prefix: 'template', count: 38 },
  { id: 'inventory', base: 'inventory', prefix: 'item', count: 55 },
  { id: 'finance', base: 'finance', prefix: 'ledger', count: 60 },
  { id: 'seller-support', base: 'seller', prefix: 'support', count: 35 },
  { id: 'oversight', base: 'oversight', prefix: 'view', count: 32 },
  { id: 'consumer', base: 'consumer', prefix: 'account', count: 28 },
  { id: 'wallet', base: 'wallet', prefix: 'feature', count: 14 },
] as const;

export type MarketplaceRouteGroup = (typeof MARKETPLACE_ROUTE_GROUPS)[number];

export const marketplaceRoutePlanTotal = MARKETPLACE_ROUTE_GROUPS.reduce(
  (total, group) => total + group.count,
  0,
);

export function getMarketplaceRouteGroup(id: string): MarketplaceRouteGroup | undefined {
  return MARKETPLACE_ROUTE_GROUPS.find((group) => group.id === id);
}
