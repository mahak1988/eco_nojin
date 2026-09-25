export interface ChainStep {
  id: string;
  token: string;
  keys: number | null;
  source: string;
}

export interface CoverageRow {
  locale: string;
  ownKeys: number;
  effectiveKeys: number;
  fromEnglish: number;
  current: boolean;
}

export interface LocaleFallbackLabels {
  metric: string;
  state: string;
  result: string;
  total: string;
  language: string;
  unavailable: string;
}

export function LocaleFallbackChain({
  merge,
  steps,
  coverage,
  labels,
  origin,
  notice,
}: {
  merge: string;
  steps: readonly ChainStep[];
  coverage: readonly CoverageRow[];
  labels: LocaleFallbackLabels;
  origin: string;
  notice: string | null;
}) {
  return (
    <div className="space-y-4">
      {notice ? (
        <p className="card p-4 text-sm text-copper" role="status" aria-live="polite">
          {notice}
        </p>
      ) : null}

      <section className="card p-5" aria-labelledby="locale-chain">
        <h2 id="locale-chain" className="field-label">
          {labels.result}
        </h2>
        <p className="num mt-2 text-xs text-ink-soft">{origin}</p>
        <pre className="mt-2 overflow-x-auto rounded-[var(--radius-m)] bg-[var(--surface-2)] p-3 text-xs text-ink">
          <code>{merge}</code>
        </pre>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
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
              {steps.map((step) => (
                <tr key={step.id} className="border-b border-line/50">
                  <th scope="row" className="py-2 pe-4 text-start font-normal">
                    <code className="num text-xs text-ink">{step.token}</code>
                  </th>
                  <td className="py-2 pe-4 text-xs text-ink-soft">
                    <code className="num">{step.source}</code>
                  </td>
                  <td className="num py-2 text-xs text-ink">
                    {step.keys === null ? labels.unavailable : step.keys}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="locale-coverage">
        <h2 id="locale-coverage" className="field-label">
          {labels.total}
        </h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-ink-soft">
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.language}
                </th>
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.total}
                </th>
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.result}
                </th>
              </tr>
            </thead>
            <tbody>
              {coverage.map((row) => (
                <tr
                  key={row.locale}
                  aria-current={row.current ? 'true' : undefined}
                  className={`border-b border-line/50 ${row.current ? 'bg-[var(--surface-2)]' : ''}`}
                >
                  <th
                    scope="row"
                    className="num py-2 pe-4 text-start font-normal text-ink"
                    lang={row.locale}
                  >
                    {row.locale}
                  </th>
                  <td className="num py-2 pe-4 text-xs text-ink-soft">{row.ownKeys}</td>
                  <td className="num py-2 text-xs text-ink">
                    {row.effectiveKeys}
                    <span aria-hidden="true" className="text-ink-faint">
                      {' '}
                      +{row.fromEnglish}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
