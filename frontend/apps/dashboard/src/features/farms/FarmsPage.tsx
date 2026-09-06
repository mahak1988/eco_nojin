import { useFarms } from '@eco/api/hooks/use-farms';
import { Badge, Card, CardBody, EmptyState, Skeleton } from '@eco/ui';
import { convertArea } from '@eco/utils';

export function FarmsPage() {
  const farms = useFarms();

  if (farms.isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  if (farms.error) {
    return <EmptyState title="Could not load farms" description={(farms.error as Error).message} />;
  }

  return (
    <div className="flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Farms</h1>
        <Badge tone="brand" variant="soft">
          {farms.data?.length ?? 0} registered
        </Badge>
      </header>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {farms.data?.map((f) => (
          <Card key={f.id} interactive>
            <CardBody className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{f.name}</h3>
                <Badge tone="neutral" variant="outline">
                  {f.primary_crop ?? '—'}
                </Badge>
              </div>
              <div className="text-sm text-ink-muted">
                {convertArea(f.area_ha, 'ha', 'ha').toFixed(2)} ha ·{' '}
                {f.centroid.lat.toFixed(3)}, {f.centroid.lon.toFixed(3)}
              </div>
              <div className="text-xs text-ink-subtle">
                Updated {new Date(f.updated_at).toLocaleDateString()}
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}