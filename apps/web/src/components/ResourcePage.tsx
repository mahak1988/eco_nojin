import { getTranslations } from 'next-intl/server';

import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { EndpointSurface } from '@/components/surface/EndpointSurface';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { type Column, DataTable } from '@/components/ui/DataTable';
import { type DataState, StateSlot } from '@/components/ui/StateSlot';
import { type ApiResult, apiGet } from '@/lib/api/client';
import { verificationOf } from '@/lib/api/surfaces';

/**
 * The template every registry-driven page is built from.
 *
 * The master plan's own answer to "985 pages" is *templates plus generation from
 * the registry* rather than 985 hand-written files. A catalog entry declares a
 * gateway endpoint; this component reads it, and renders one of the five states
 * the plan requires of every data-bearing surface.
 *
 * What it deliberately does not do is invent anything. There is no fallback
 * fixture, no placeholder count and no "verified" flag that is not backed by a
 * real response. A page whose endpoint is unreachable says so and names the
 * path, which is the project's standing rule: real data or an explicit label.
 *
 * Two extraction modes, because the gateway returns both shapes:
 *
 *   - `rows` reads an array from a field path, e.g. `products` in
 *     `{ products: [...] }`. The field path is declared, not guessed, so a shape
 *     change surfaces as an empty state with the path named rather than as a
 *     silently blank table.
 *   - `record` renders an object as label/value cards, for the health and status
 *     endpoints that return a flat document.
 */

export type ResourceTone = 'info' | 'success' | 'warn' | 'bad';

/**
 * `Row` is the type of one row; `Payload` is the type the gateway returned.
 *
 * They are usually the same — for an object payload the generator declares
 * `Record<string, unknown>` and every row is that shape — but they diverge for
 * every contract that returns a bare array. `GET
 * /api/v1/commerce/orders/{order_id}/transitions` (`commerce.py:271`) answers a
 * bare `list[str]`, so the payload is `string[]` and each row is a `string`.
 * With one parameter, `rowKey` and `columns` would be typed on the payload and
 * the columns would be rejected.
 *
 * `Payload` defaults to `Row`, so the 132 generated pages and every existing call
 * site are unaffected.
 */
export interface ResourcePageProps<Row, Payload = Row> {
  /** The catalogue slug this page was generated from, e.g. `market-cart`. */
  slug: string;
  locale: string;
  /** Heading text, already resolved by the caller from `pageMeta`. */
  title: string;
  /** Lead paragraph, resolved from `pageMeta`. */
  description: string;
  /** Registered gateway path. Never a substitute. */
  path: string;
  /** Rendered result of `apiGet` for `path`. */
  result: ApiResult<Payload>;
  /** Table mode, or `record` for a flat document. */
  mode: 'rows' | 'record';
  /** Field holding the array, for `mode: 'rows'`. */
  rowsKey?: string;
  columns?: Column<Row>[];
  rowKey?: (row: Row) => string;
  /** Copy for the five states, from the catalogue. */
  labels: {
    loading: string;
    empty: string;
    error: string;
    offline: string;
    partial: string;
    action: string;
  };
  /** Tone for the provenance stamp, for capability pages. */
  tone?: ResourceTone;
  /** Extra content under the table, for callers that have more to say. */
  /**
   * Extra content under the table. Given a function, it receives what the page
   * would otherwise have to recompute — the row count and the resolved state — so
   * a surface can say "your search matched nothing" without reaching back into
   * the payload a second time.
   */
  children?:
    | React.ReactNode
    | ((context: { total: number; state: DataState; path: string }) => React.ReactNode);
}

const MAX_PREVIEW = 50;

function readRows<T>(data: unknown, rowsKey: string | undefined): T[] {
  if (Array.isArray(data)) return data as T[];
  if (!rowsKey || typeof data !== 'object' || data === null) return [];
  const value = (data as Record<string, unknown>)[rowsKey];
  return Array.isArray(value) ? (value as T[]) : [];
}

/**
 * Build columns from the response when the caller declares none.
 *
 * A registry entry names a route, not a schema, so inventing a column list would
 * mean guessing field names that may not exist. Reading the keys off the first
 * row shows whatever the gateway actually returned, and a shape change shows up
 * as a changed table rather than as a table of empty cells.
 */
function inferColumns<T>(rows: T[], declared: Column<T>[] | undefined): Column<T>[] {
  if (declared && declared.length > 0) return declared;
  const first = rows[0];
  if (!first || typeof first !== 'object' || first === null) return [];
  return Object.keys(first as Record<string, unknown>).map((key) => ({
    key,
    header: key.replace(/[_-]/g, ' '),
    // A value that is entirely numeric in the sample is presented as one, so the
    // tabular-digit treatment applies and it mirrors correctly under RTL.
    numeric: rows.every((row) => {
      const value = (row as Record<string, unknown>)[key];
      return typeof value === 'number' || typeof value === 'string' || value === null;
    }),
  }));
}

const isOffline = (result: ApiResult<unknown>): boolean => !result.ok && result.status === 0;

export async function ResourcePage<Row, Payload = Row>({
  slug,
  locale,
  title,
  description,
  path,
  result,
  mode,
  rowsKey,
  columns,
  rowKey,
  labels,
  tone = 'info',
  children,
}: ResourcePageProps<Row, Payload>) {
  // A contract that declares no field is a different case from one that declares
  // an array, and the codebase already has a renderer for it. Delegating rather
  // than reimplementing means the "the payload says it is verified" rule lives in
  // one place — `verificationOf` — rather than in two renderers that can drift.
  if (mode === 'record') {
    return (
      <EndpointSurface
        locale={locale}
        source={path}
        title={title}
        description={description}
        result={result}
        emptyTitle={labels.empty}
        emptyDescription={labels.empty}
        backHref={`/${locale}`}
      >
        {typeof children === 'function' ? null : children}
      </EndpointSurface>
    );
  }

  const status = await getTranslations('statusLine');

  const rows = result.ok && mode === 'rows' ? readRows<Row>(result.data, rowsKey) : [];
  const total = rows.length;

  const state = !result.ok
    ? isOffline(result)
      ? 'offline'
      : 'error'
    : total === 0
      ? 'empty'
      : total > MAX_PREVIEW
        ? 'partial'
        : 'ready';

  const extra = typeof children === 'function' ? children({ total, state, path }) : children;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <Badge tone={result.ok ? 'success' : 'warn'} dot>
            {result.ok ? status('realData') : status('unavailable')}
          </Badge>
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
        <div className="mt-4">
          {/* The stamp names the contract, and is verified only on a real 2xx. */}
          <ProvenanceStamp
            source={path}
            label={title}
            verified={result.ok && verificationOf(result.data)}
            method={path}
            data-tone={tone}
          />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <StateSlot
          state={state}
          labels={labels}
          density="cozy"
          detail={
            result.ok ? `${path} · ${total}` : `${path} · ${result.ok ? '' : result.status || '—'}`
          }
        >
          {mode === 'rows' && rowKey ? (
            <Card density="compact">
              {(() => {
                const tableColumns = inferColumns(rows, columns);
                if (tableColumns.length === 0) return null;
                return (
                  <>
                    <DataTable
                      columns={tableColumns}
                      rows={rows.slice(0, MAX_PREVIEW)}
                      rowKey={rowKey}
                      caption={title}
                      density="compact"
                      emptyLabel={labels.empty}
                    />
                    {total > MAX_PREVIEW ? (
                      <p className="num mt-3 text-xs text-ink-soft">{total - MAX_PREVIEW}</p>
                    ) : null}
                  </>
                );
              })()}
            </Card>
          ) : null}
        </StateSlot>
      </section>

      {extra ? <section className="mx-auto max-w-5xl px-6 pb-12">{extra}</section> : null}

      <p className="mx-auto max-w-5xl px-6 pb-12 text-xs text-ink-soft">
        {/* `slug` is carried so a generated page can be traced back to its
            catalogue entry without reading the filesystem. */}
        <span className="num">{slug}</span>
      </p>
    </main>
  );
}

export default ResourcePage;

/**
 * Builds the `page.tsx` body for a registry entry.
 *
 * Kept beside the component so the generator and the renderer cannot drift: both
 * import this, so a change to the state contract reaches every generated page at
 * once instead of 114 files needing an edit.
 */
export async function resourceLabels(): Promise<ResourcePageProps<never>['labels']> {
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const market = await getTranslations('market.template');
  const offline = await getTranslations('offline');
  return {
    loading: status('noData'),
    empty: market('unavailableDescription'),
    error: common('error'),
    offline: offline('description'),
    partial: market('unavailableDescription'),
    action: common('retry'),
  };
}

/** Fetch helper that keeps the generated pages to a single call site. */
export function fetchResource<T>(path: string): Promise<ApiResult<T>> {
  return apiGet<T>(path);
}
