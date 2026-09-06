import { useDashboardFull, useDashboardProjects } from '@eco/api';
import { Badge, Card, CardBody, CardHeader, EmptyState, Skeleton } from '@eco/ui';
import { formatCompact } from '@eco/utils';

type ProjectRow = {
  id?: string;
  name?: string;
  region_name?: string;
  area_ha?: number;
  created_at?: string;
  [key: string]: unknown;
};

export function DashboardHome() {
  const full = useDashboardFull();
  const projects = useDashboardProjects();

  if (full.error) {
    return (
      <EmptyState
        title="Cannot reach backend"
        description={(full.error as Error).message}
      />
    );
  }

  if (full.isLoading || !full.data) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const data = full.data;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Workspace overview</h1>
          <p className="text-sm text-ink-muted">
            {data.timestamp ? `Generated ${new Date(data.timestamp).toLocaleString()}` : 'Live snapshot'}
          </p>
        </div>
        <Badge tone="success" variant="soft">Live</Badge>
      </header>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Projects" value={data.projects?.total ?? 0} icon="📊" />
        <Kpi label="Total area" value={data.projects?.total_area_hectares ?? 0} icon="🌾" suffix="ha" />
        <Kpi label="Carbon credits" value={data.carbon?.total_credits ?? 0} icon="🌱" />
        <Kpi label="Active motors" value={data.platform?.active_motors ?? 0} icon="🧠" />
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Weather days" value={data.weather?.days_recorded ?? 0} icon="🌤️" />
        <Kpi label="Avg temperature" value={data.weather?.avg_temperature_c ?? 0} icon="🌡️" suffix="°C" />
        <Kpi label="Avg NDVI" value={data.satellite?.avg_ndvi ?? 0} icon="🛰️" />
        <Kpi label="Soil profiles" value={data.soil?.total_profiles ?? 0} icon="🌍" />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <h2 className="text-base font-semibold">Recent projects</h2>
          </CardHeader>
          <CardBody>
            {projects.isLoading ? (
              <Skeleton className="h-32" />
            ) : (
              <ProjectsTable rows={(projects.data ?? []) as ProjectRow[]} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Platform</h2>
          </CardHeader>
          <CardBody className="grid grid-cols-2 gap-3 text-center text-sm">
            <Tile label="Tables" value={data.platform?.total_tables ?? 0} />
            <Tile label="Services" value={data.platform?.total_services ?? 0} />
            <Tile label="Endpoints" value={data.platform?.api_endpoints ?? 0} />
            <Tile label="Motors" value={data.platform?.active_motors ?? 0} />
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

function Kpi({ label, value, icon, suffix }: { label: string; value: number; icon: string; suffix?: string }) {
  return (
    <Card>
      <CardBody className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-ink-muted">{label}</span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-brand-700">{formatCompact(value)}</span>
          {suffix && <span className="text-xs text-ink-muted">{suffix}</span>}
          <span className="ms-auto text-xl">{icon}</span>
        </div>
      </CardBody>
    </Card>
  );
}

function Tile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-surface-muted p-3">
      <div className="text-lg font-semibold text-brand-700">{formatCompact(value)}</div>
      <div className="text-xs text-ink-muted">{label}</div>
    </div>
  );
}

function ProjectsTable({ rows }: { rows: ProjectRow[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-ink-muted">No projects reported by backend yet.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-start text-xs uppercase text-ink-muted">
          <tr>
            <th className="py-2 text-start">Name</th>
            <th className="py-2 text-start">Region</th>
            <th className="py-2 text-start">Area (ha)</th>
            <th className="py-2 text-start">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ink/5">
          {rows.slice(0, 8).map((row, idx) => (
            <tr key={row.id ?? idx}>
              <td className="py-2">{row.name ?? '—'}</td>
              <td className="py-2">{row.region_name ?? '—'}</td>
              <td className="py-2">{row.area_ha?.toLocaleString('fa-IR') ?? '—'}</td>
              <td className="py-2 text-ink-muted">
                {row.created_at ? new Date(row.created_at).toLocaleDateString('fa-IR') : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}