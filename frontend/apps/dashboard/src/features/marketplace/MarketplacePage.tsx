import { Card, CardBody, CardHeader, EmptyState } from '@eco/ui';

export function MarketplacePage() {
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">🛒 Marketplace</h1>
        <p className="text-sm text-ink-muted">Buy and sell verified carbon credits.</p>
      </header>
      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Listings</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            title="Marketplace coming online"
            description="The backend exposes /marketplace endpoints; the trading UI is part of Phase 3."
          />
        </CardBody>
      </Card>
    </div>
  );
}