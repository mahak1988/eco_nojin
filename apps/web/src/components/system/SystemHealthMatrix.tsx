import { type DotState, StatusDot } from '@/components/StatusDot';

export interface HealthRow {
  id: string;
  label: string;
  token: string;
  state: DotState;
  stateLabel: string;
  result: string | null;
}

export interface HealthMatrixLabels {
  metric: string;
  state: string;
  result: string;
  caption: string;
}

export function SystemHealthMatrix({
  rows,
  labels,
  emptyLabel,
}: {
  rows: readonly HealthRow[];
  labels: HealthMatrixLabels;
  emptyLabel: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{labels.caption}</caption>
        <thead>
          <tr className="border-b border-line text-ink-soft">
            <th scope="col" className="py-2 text-start font-medium">
              {labels.metric}
            </th>
            <th scope="col" className="py-2 text-start font-medium">
              {labels.state}
            </th>
            <th scope="col" className="py-2 text-start font-medium">
              {labels.result}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={3} className="py-3 text-sm text-copper">
                {emptyLabel}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id} className="border-b border-line/50">
                <th scope="row" className="py-2 pe-4 text-start font-normal text-ink">
                  <span className="block">{row.label}</span>
                  <code className="num mt-0.5 block text-[11px] text-ink-faint">{row.token}</code>
                </th>
                <td className="py-2 pe-4">
                  <StatusDot state={row.state} label={row.stateLabel} />
                </td>
                <td className="num py-2 text-xs text-ink-soft">{row.result ?? '—'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
