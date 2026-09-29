import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import type { ReactNode } from 'react';

import { Badge } from '@/components/ui/Badge';

import { type CheckResult, number, type SpecParam, scalar, type ToolSpec } from './hydroma';

/**
 * The three output scenes T07 allows — table, chart, record — and the sticky
 * input panel that sits beside them.
 *
 * All of it is server-rendered, and the tables are hand-rolled rather than
 * delegated to the house `DataTable`. `DataTable` is a client island whose
 * `columns[].render` and `rowKey` are functions, and §3.3 of the plan names three
 * islands — MapLibre, deck.gl, WebGPU — and says everything else stays an RSC.
 * A registry table has no client behaviour worth a bundle, so these pages ship
 * no JavaScript at all.
 */

/** Humanises a contract field name. Language-neutral, like a column header. */
function header(key: string): string {
  return key.replace(/[_-]/g, ' ');
}

/* -------------------------------------------------------------------------- */
/* The sticky input panel                                                     */
/* -------------------------------------------------------------------------- */

/**
 * The parameter contract, read from the tool's own spec.
 *
 * T07 requires a sticky input panel for a route that runs something. These
 * pages bind a *metadata* GET, so the panel states the contract the POST would
 * validate rather than pretending to run it: parameter names, kinds, units,
 * defaults and option sets come straight out of `_SPECS`, and the run endpoint is
 * named so a reader can repeat the question from a terminal. Nothing here is
 * editable, because nothing here is submitted — a control that cannot change the
 * output is a decoration, and the plan's complaint about the 110 single-pattern
 * pages is precisely that.
 */
export async function InputContract({
  params,
  runPath,
}: {
  params: readonly SpecParam[];
  runPath: string;
}) {
  const t = await getTranslations('hydroma.instrument');
  // A type predicate, not a bare filter: `SpecParam.name` is optional because the
  // contract models it as optional, and the list is keyed by name.
  const list = params.filter(
    (param): param is SpecParam & { name: string } => typeof param.name === 'string',
  );

  return (
    <div className="flex flex-col gap-3">
      {list.length === 0 ? (
        <p className="text-xs text-ink-soft">{t('noParams')}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {list.map((param) => (
            <li
              key={param.name}
              className="rounded-[var(--radius-s)] border border-line bg-surface px-3 py-2"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="num text-sm text-ink">{param.name}</span>
                <Badge tone={param.optional ? 'neutral' : 'info'} density="dense">
                  {param.optional ? t('optional') : t('required')}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-ink-soft">{param.label ?? header(param.name)}</p>
              <dl className="num mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-ink-faint">
                <div className="flex gap-1">
                  <dt>{t('kind')}</dt>
                  <dd>{scalar(param.kind)}</dd>
                </div>
                {param.unit ? (
                  <div className="flex gap-1">
                    <dt>{t('unit')}</dt>
                    <dd>{param.unit}</dd>
                  </div>
                ) : null}
                {param.default !== undefined ? (
                  <div className="flex gap-1">
                    <dt>{t('default')}</dt>
                    <dd>{scalar(param.default)}</dd>
                  </div>
                ) : null}
              </dl>
              {Array.isArray(param.options) && param.options.length > 0 ? (
                <p className="num mt-1 break-words text-xs text-ink-faint">
                  {t('options')}
                  {param.options.map((option) => scalar(option)).join(' · ')}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      <p className="num break-all text-xs text-ink-soft">{t('runIsPost', { path: runPath })}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Scene 1 — the table                                                        */
/* -------------------------------------------------------------------------- */

/** One row of the tool table, flattened so every cell is a primitive. */
interface SpecRow {
  id: string;
  name: string;
  description: string;
  reference: string;
  paramCount: number;
}

function toRows(specs: readonly ToolSpec[]): SpecRow[] {
  return specs.map((spec, index) => ({
    id: String(spec.id ?? `spec-${index}`),
    name: scalar(spec.name_en),
    description: scalar(spec.description),
    reference: scalar(spec.reference),
    paramCount: (spec.params ?? []).length,
  }));
}

/**
 * The family's tool table, every row linking to its own instrument page.
 *
 * `paramCount` is the number of declared parameters, which is the one number on
 * this page a reader can act on: it is the size of the input contract they are
 * about to fill in.
 */
export function SpecTable({
  specs,
  detailBase,
  caption,
  nameHeader,
  descriptionHeader,
  referenceHeader,
  paramsHeader,
}: {
  specs: readonly ToolSpec[];
  /** Localised base of the detail route, e.g. `/fa/hydroma/soil`. */
  detailBase: string;
  caption: string;
  nameHeader: string;
  descriptionHeader: string;
  referenceHeader: string;
  paramsHeader: string;
}) {
  const rows = toRows(specs);
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="text-start text-xs text-ink-faint">{caption}</caption>
        <thead>
          <tr className="border-b border-line-strong">
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              id
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {nameHeader}
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {descriptionHeader}
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {referenceHeader}
            </th>
            <th scope="col" className="py-2 text-end text-xs font-semibold text-ink-soft">
              {paramsHeader}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-line align-top">
              <th scope="row" className="num py-2 pe-3 text-start font-normal">
                <Link
                  href={`${detailBase}/${encodeURIComponent(row.id)}`}
                  className="text-action underline decoration-line-strong underline-offset-2"
                >
                  {row.id}
                </Link>
              </th>
              <td className="py-2 pe-3 text-ink">{row.name}</td>
              <td className="py-2 pe-3 text-ink-soft">{row.description}</td>
              <td className="py-2 pe-3 text-ink-soft">{row.reference}</td>
              <td className="num py-2 text-end text-ink">{number(row.paramCount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Scene 2 — the chart                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Every verification check, as the ratio of its error to the tolerance it was
 * judged against.
 *
 * `formula_checks.py:62` publishes `expected`, `actual` and `tolerance` and calls
 * a check passed when `|expected − actual| <= tolerance`. So
 * `|expected − actual| / tolerance` is the one dimensionless quantity the
 * contract publishes about a check's fit, and at or above 1 the check failed.
 * Plotting anything else — a pass count dressed as a trend, a latency bar —
 * would be a chart of a number the reader cannot audit against the source.
 *
 * A non-numeric comparison (`expected == actual`) has no ratio, so it is drawn
 * full width and labelled as an exact comparison rather than given a ratio it
 * does not have.
 */
export async function ToleranceChart({ checks }: { checks: readonly CheckResult[] }) {
  const t = await getTranslations('hydroma.chart');
  if (checks.length === 0) return null;

  return (
    <figure className="flex flex-col gap-2">
      <figcaption className="text-xs text-ink-soft">{t('caption')}</figcaption>
      <ul className="flex flex-col gap-1">
        {checks.map((check) => {
          const expected = typeof check.expected === 'number' ? check.expected : null;
          const actual = typeof check.actual === 'number' ? check.actual : null;
          const tolerance = typeof check.tolerance === 'number' ? check.tolerance : null;
          const ratio =
            expected === null || actual === null || tolerance === null || tolerance === 0
              ? null
              : Math.abs(expected - actual) / tolerance;
          const exact = ratio === null;
          const width = exact ? 100 : Math.max(1.5, Math.min(100, ratio * 20));
          return (
            <li key={check.id} className="flex items-center gap-2 text-xs">
              <span className="num min-w-0 flex-1 truncate text-ink-soft">{check.id}</span>
              <span
                aria-hidden="true"
                className="h-2 w-24 shrink-0 overflow-hidden rounded-[var(--radius-s)] bg-line"
              >
                <span
                  className="block h-full rounded-[var(--radius-s)]"
                  style={{
                    inlineSize: `${width}%`,
                    backgroundColor: check.passed ? 'var(--color-forest)' : 'var(--color-clay)',
                  }}
                />
              </span>
              <span className="num w-24 shrink-0 text-end text-ink-faint">
                {exact ? t('exact') : t('ratio', { value: number(ratio) })}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-ink-faint">{t('legend')}</p>
    </figure>
  );
}

/* -------------------------------------------------------------------------- */
/* Scene 3 — the record                                                       */
/* -------------------------------------------------------------------------- */

/**
 * A flat document as label/value rows.
 *
 * `ResourcePage` delegates its `record` mode to `EndpointSurface`, which brings
 * its own chrome and its own regions. T07 is a different archetype, so the
 * record is read here rather than nested inside a page that is already one.
 */
export function RecordScene({
  entries,
  caption,
}: {
  entries: readonly { label: string; value: ReactNode }[];
  caption: string;
}) {
  return (
    <table className="w-full border-collapse text-sm">
      <caption className="text-start text-xs text-ink-faint">{caption}</caption>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.label} className="border-b border-line align-top">
            <th
              scope="row"
              className="w-2/5 py-2 pe-3 text-start text-xs font-medium text-ink-soft"
            >
              {entry.label}
            </th>
            <td className="num py-2 text-ink">{entry.value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
