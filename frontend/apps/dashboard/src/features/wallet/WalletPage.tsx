import { Card, CardBody, CardHeader, EmptyState } from '@eco/ui';

export function WalletPage() {
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">💰 Carbon wallet</h1>
        <p className="text-sm text-ink-muted">Eco-wallet balances across standards.</p>
      </header>
      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Balances</h2>
        </CardHeader>
        <CardBody>
          <EmptyState
            title="Wallet data will load once auth is wired"
            description="Phase 3 connects the Supabase session to /api/v1/carbon/wallet."
          />
        </CardBody>
      </Card>
    </div>
  );
}