import { getTranslations } from 'next-intl/server';
import type { ReactNode } from 'react';

import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { TemplateRegion } from '@/components/templates/TemplateFrame';
import { Badge } from '@/components/ui/Badge';
import { Card, type CardDensity } from '@/components/ui/Card';
import { type Column, DataTable } from '@/components/ui/DataTable';
import { type DataState, StateSlot } from '@/components/ui/StateSlot';
import {
  type PageDensity,
  type RequiredRegion,
  requireTemplateForEntry,
  type TemplateLabels,
} from '@/lib/design/page-templates';
import { getCatalogEntry } from '@/lib/domains/page-catalog';

/**
 * The admin and workspace catalogue surfaces, rendered on the archetype the plan
 * assigns them.
 *
 * ## Why this file exists and is not `TemplateFrame`
 *
 * `TemplateFrame` owns the four non-negotiables of §4.1 — the five states
 * through `StateSlot`, the placed provenance stamp, the declared region order and
 * one `<h1>` — and every page in this subtree wants all four. What it cannot be
 * used for is its outer `<main id="main">`: `admin/layout.tsx:77` and
 * `workspace/layout.tsx` both already render one, so mounting `LedgerPage` here
 * would emit a second `<main>` and a second `id="main"` on every page, which is
 * invalid document structure and a duplicate landmark for assistive technology.
 * Those two layouts are outside this workstream, so the frame is composed here
 * from the same primitives instead: `StateSlot` for the states,
 * `ProvenanceStamp` for the source, `TemplateRegion` for the `data-region`
 * contract, and `requireTemplateForEntry` for the archetype.
 *
 * The archetype is never hard-coded. It is resolved from the real catalogue entry
 * by the real partition, so a page that claims the wrong region order fails
 * instead of drifting: `requireTemplateForEntry` throws when no archetype claims
 * a route or when two do. All 25 routes in this subtree were checked against it
 * and each resolves to exactly one template — T08 for the admin context and the
 * workspace grids, T04 for the single records, T10 for the two statements.
 *
 * ## The `partial` state, decided deliberately
 *
 * §4.5 requires five states and `StateSlot` renders all of them, so the copy for
 * all five is resolved here. What is decided here is *when* `partial` is passed.
 *
 * `StateSlot` returns its children only for `ready` (`StateSlot.tsx:100`): on
 * `partial` it replaces the data with a message. A page that fetched 60 rows and
 * sliced them to a 50-row preview would therefore hand the reader a sentence and
 * nothing else, discarding 50 real, stamped records to make a disclosure it could
 * have printed alongside the table. That is a worse outcome than the one §4.5 is
 * written to prevent, and `StateSlot` is not in this workstream's ownership.
 *
 * So this surface reports `partial` only when there is nothing to show, which for
 * these contracts is never, and discloses a truncated preview as a labelled line
 * inside the data region instead — the reader keeps the rows *and* the disclosure.
 * `loading` is reached through the `loading.tsx` boundary this subtree ships;
 * `empty`, `error` and `offline` are resolved from the real response.
 */

/** Rows a table shows before the page says it is showing a subset. */
export const PREVIEW_LIMIT = 50;

const DENSITY_GAP: Record<PageDensity, string> = {
  comfortable: 'gap-6',
  compact: 'gap-4',
  dense: 'gap-2',
};

/** `StateSlot` speaks `cozy | compact | dense`; the plan speaks `comfortable`. */
const SLOT_DENSITY: Record<PageDensity, CardDensity> = {
  comfortable: 'cozy',
  compact: 'compact',
  dense: 'dense',
};

/** The two fragment namespaces this subtree owns. Nothing else may be added. */
export type LedgerNamespace = 'admin' | 'workspace';

/* -------------------------------------------------------------------------- */
/*  Contract reading                                                           */
/* -------------------------------------------------------------------------- */

export interface LedgerResult<T> {
  ok: boolean;
  data?: T;
  status: number;
  error?: string;
}

/**
 * The five states of §4.5, decided once.
 *
 * `status === 0` is a transport failure rather than a server error — it is what
 * `adminGet`/`workspaceGet` report when `fetch` throws, which is what an offline
 * or degraded reader actually sees. Telling that reader the server is down is the
 * exact failure `StateSlot` exists to prevent, so it gets its own state.
 */
export function resolveLedgerState<T>(result: LedgerResult<T>, total: number): DataState {
  if (!result.ok) return result.status === 0 ? 'offline' : 'error';
  if (total === 0) return 'empty';
  return 'ready';
}

/**
 * Reads the declared field, or reports that there is none.
 *
 * A bare array is its own rows. Anything else needs the key the router returns,
 * and an absent key yields an empty array — which becomes the `empty` state
 * naming the contract, never a row set invented from the route name. The rule
 * exists because `ResourcePage` renders its *empty* state over a 200 whose field
 * it guessed wrong, which reads to a reader exactly like "there is no data".
 */
export function readRows<T>(data: unknown, rowsKey?: string): T[] {
  if (Array.isArray(data)) return data as T[];
  if (!rowsKey || typeof data !== 'object' || data === null) return [];
  const value = (data as Record<string, unknown>)[rowsKey];
  return Array.isArray(value) ? (value as T[]) : [];
}

/** A field of a record payload, read without lying about its type. */
export function record(data: unknown): Record<string, unknown> {
  return typeof data === 'object' && data !== null && !Array.isArray(data)
    ? (data as Record<string, unknown>)
    : {};
}

/** A JSON value rendered as text. Never invents a value for an absent field. */
export function scalar(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map((item) => scalar(item)).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** A number, grouped and Latin so it mirrors correctly inside an RTL document. */
export function number(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return scalar(value);
  return value.toLocaleString('en-US', { maximumFractionDigits: 6 });
}

/** Interpolates a dynamic route segment, percent-encoded, or reports its absence. */
export function segment(value: string | undefined): string {
  return encodeURIComponent((value ?? '').trim());
}

/**
 * A dynamic segment the contract declares as an integer.
 *
 * `admin_content.py:200` and `:213` declare `item_id: int`, so a request carrying
 * anything else is answered `422` by the gateway. Reading the segment as a number
 * first lets the page say *why* it made no request instead of reporting a
 * validation failure it could have predicted, and it stops a string from being
 * interpolated into a path the contract never declared.
 */
export function integerSegment(value: string | undefined): number | null {
  const raw = (value ?? '').trim();
  if (!/^\d{1,18}$/.test(raw)) return null;
  const parsed = Number(raw);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

/* -------------------------------------------------------------------------- */
/*  Copy                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * `TemplateLabels` for the archetypes, resolved from this subtree's fragment.
 *
 * Every string lives in `admin.ledger.*` or `workspace.ledger.*`, never in the
 * component. A component library that carries its own English cannot be
 * translated, which is the defect `StateSlot`'s own doc comment records, and the
 * thirteen locales that are not English would get a page of English chrome around
 * a translated heading.
 */
export async function ledgerLabels(namespace: LedgerNamespace): Promise<TemplateLabels> {
  const t = await getTranslations(`${namespace}.ledger`);

  return {
    loading: t('states.loading'),
    empty: t('states.empty'),
    error: t('states.error'),
    offline: t('states.offline'),
    partial: t('states.partial'),
    action: t('states.retry'),
    provenance: t('provenance'),
    live: t('live'),
    unavailable: t('unavailable'),
    footer: t('footer'),
    regions: {
      title: t('regions.title'),
      status: t('regions.status'),
      provenance: t('regions.provenance'),
      filters: t('regions.filters'),
      state: t('regions.state'),
      data: t('regions.data'),
      actions: t('regions.actions'),
      summary: t('regions.summary'),
      detail: t('regions.detail'),
      notes: t('regions.notes'),
      print: t('regions.print'),
      footer: t('regions.footer'),
    },
  };
}

/* -------------------------------------------------------------------------- */
/*  The surface                                                                */
/* -------------------------------------------------------------------------- */

export interface LedgerSurfaceProps {
  /** Catalogue path, e.g. `/admin/errors`. Resolves the archetype. */
  catalogPath: string;
  namespace: LedgerNamespace;
  title: string;
  description: string;
  /** The gateway contract this page actually called, with its path segments resolved. */
  path: string;
  /** Catalogue slug, printed in the footer so a page is traceable to its entry. */
  slug: string;
  state: DataState;
  total: number;
  /** Whether the gateway answered. Drives the live/unavailable badge. */
  ok: boolean;
  /** Verified only on a real 2xx whose payload asserts it. Never defaulted true. */
  verified?: boolean;
  /** Second line of the state slot: `path · count`. */
  stateDetail?: string;
  /** The `data` region. */
  data: ReactNode;
  /**
   * Replaces the generated `title` region.
   *
   * The workspace context owns its heading — `WorkspacePageHeader` renders the
   * registry's own label and lead keys and a breadcrumb of real destinations — and
   * that component already emits an `<h1>`. Passing it here keeps exactly one
   * `<h1>` on the page while the region contract is unchanged, instead of stacking
   * a second heading next to it.
   */
  heading?: ReactNode;
  detail?: ReactNode;
  filters?: ReactNode;
  actions?: ReactNode;
  summary?: ReactNode;
  notes?: ReactNode;
}

export async function LedgerSurface({
  catalogPath,
  namespace,
  title,
  description,
  path,
  slug,
  state,
  total,
  ok,
  verified,
  stateDetail,
  data,
  heading,
  detail,
  filters,
  actions,
  summary,
  notes,
}: LedgerSurfaceProps) {
  const entry = getCatalogEntry(catalogPath);
  if (!entry) {
    throw new Error(`no catalogue entry for "${catalogPath}"; the page is not in the inventory`);
  }
  // Throws when no archetype claims the route or when two do. That is deliberate:
  // a silent fallback would render a page whose layout no longer matches the plan.
  const template = requireTemplateForEntry(entry);
  const labels = await ledgerLabels(namespace);
  const gap = DENSITY_GAP[template.density];
  const anchor = template.provenance.anchor;

  const stamp = (
    <div
      data-provenance-region={anchor}
      className="mb-2 flex flex-wrap items-center justify-end gap-2"
    >
      <ProvenanceStamp source={path} label={labels.provenance} verified={verified} />
    </div>
  );

  /**
   * True when the stamp cannot sit on the numbers and moves to its own region.
   *
   * `TemplateFrame` computes this as `anchor === 'data' && state !== 'ready'`,
   * which is right while the anchored region is always rendered. It is not enough
   * here: the T04 and T10 archetypes anchor on `summary`, and a page that has
   * nothing to summarise passes no summary node at all, so the stamp would have
   * nowhere to land on a failed request and the page would name no contract. Since
   * the state is not `ready` there are no numbers to sit beside either way, the
   * stamp goes to the `provenance` region and the anchored region is left unstamped,
   * so it still appears exactly once.
   */
  const inHeader = state !== 'ready';

  /** Stamped regions get the stamp above their content, and only ever once. */
  const withStamp = (name: RequiredRegion, content: ReactNode): ReactNode =>
    inHeader || name !== anchor ? (
      content
    ) : (
      <>
        {stamp}
        {content}
      </>
    );

  const supplied: Partial<Record<RequiredRegion, ReactNode>> = {
    filters,
    actions,
    detail,
    summary,
    notes,
  };

  const region = (name: RequiredRegion): ReactNode => {
    if (name === 'title') {
      if (heading) {
        return (
          <div data-region="title" className="flex flex-col gap-3">
            {heading}
          </div>
        );
      }
      return (
        <header data-region="title" className="flex flex-col gap-3">
          <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">{title}</h1>
          <p className="max-w-2xl text-sm text-pretty text-ink-soft">{description}</p>
        </header>
      );
    }

    if (name === 'status') {
      return (
        <div data-region="status" className="flex flex-wrap items-center gap-2">
          <Badge tone={ok ? 'success' : 'warn'} dot density="dense">
            {ok ? labels.live : labels.unavailable}
          </Badge>
        </div>
      );
    }

    // `state` and `data` are one unit: the slot reports the five states and its
    // children are the data region, so the rendered order is the declared order.
    if (name === 'data') return null;
    if (name === 'state') {
      return (
        <TemplateRegion region="state" title={labels.regions.state} className={gap}>
          <StateSlot
            state={state}
            labels={labels}
            density={SLOT_DENSITY[template.density]}
            detail={stateDetail ?? `${path} · ${total}`}
          >
            <TemplateRegion region="data" className={gap}>
              {withStamp('data', data)}
            </TemplateRegion>
          </StateSlot>
        </TemplateRegion>
      );
    }

    if (name === 'provenance') {
      if (!inHeader && anchor !== 'provenance') return null;
      return (
        <TemplateRegion region="provenance" title={labels.regions.provenance} className={gap}>
          {stamp}
        </TemplateRegion>
      );
    }

    if (name === 'footer') {
      return (
        <TemplateRegion region="footer" title={labels.regions.footer} className={gap}>
          <p className="text-xs text-ink-faint">
            {labels.footer} <span className="num">{slug}</span>
          </p>
        </TemplateRegion>
      );
    }

    const content = supplied[name];
    if (content === undefined) return null;

    if (name === 'filters') {
      return (
        <TemplateRegion
          region="filters"
          title={labels.regions.filters}
          className="sticky start-0 top-16 z-30 rounded-m border border-line bg-surface p-3"
        >
          {withStamp('filters', content)}
        </TemplateRegion>
      );
    }

    return (
      <TemplateRegion region={name} title={labels.regions[name]} className={gap}>
        {withStamp(name, content)}
      </TemplateRegion>
    );
  };

  return (
    <div data-page-template={template.plan} data-density={template.density} className={gap}>
      {template.regions.map((name) => region(name))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Regions                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * A disclosure that some field of a real contract is not a measurement.
 *
 * Several contracts in this subtree return a constant where their schema implies
 * a reading: `admin_overview.py:88-97` hard-codes every channel's status and
 * latency, `admin_models.py:33-65` is a literal model list with truncated fake
 * digests, `admin_security.py:105-117` hard-codes the country breakdown and the
 * suspicious-activity rows. The row is real — the gateway really did answer — so
 * the cell is rendered as a label saying so, and never as the number.
 */
export function UnmeasuredCell({ label }: { label: string }) {
  return <span className="text-xs text-copper">{label}</span>;
}

/** The page-level notice for a payload in which no field is a measurement. */
export function PlaceholderNotice({ heading, body }: { heading: string; body: string }) {
  return (
    <Card density="compact" className="border-l-2 border-l-copper">
      <h3 className="text-sm font-semibold text-ink">{heading}</h3>
      <p className="mt-1 text-sm text-ink-soft">{body}</p>
    </Card>
  );
}

/** A record rendered as label/value rows, for the T04 and T10 archetypes. */
export function RecordList({
  fields,
  caption,
}: {
  fields: readonly { label: string; value: ReactNode }[];
  caption: string;
}) {
  return (
    <dl className="grid gap-2 sm:grid-cols-[minmax(0,16rem)_minmax(0,1fr)]">
      {fields.map((field) => (
        <div key={field.label} className="contents">
          <dt className="text-xs text-ink-soft">{field.label}</dt>
          <dd className="num break-words text-sm text-ink">
            {field.value === null || field.value === undefined || field.value === ''
              ? '—'
              : field.value}
          </dd>
        </div>
      ))}
      <p className="sr-only">{caption}</p>
    </dl>
  );
}

/** The grid every T08 page in this subtree is a table of. */
export function LedgerTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  emptyLabel,
}: {
  columns: readonly Column<T>[];
  rows: readonly T[];
  rowKey: (row: T) => string;
  caption: string;
  emptyLabel: string;
}) {
  return (
    <Card density="compact">
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={rowKey}
        caption={caption}
        density="compact"
        emptyLabel={emptyLabel}
      />
    </Card>
  );
}

/**
 * A stable key for a row whose contract declares no single unique column.
 *
 * `DataTable` takes `rowKey: (row: T) => string` — one argument, deliberately, so
 * a key cannot be built from a position that sorting would move. Several of these
 * contracts publish no primary key at all (`finance/ledger/entries` projects a dict
 * whose `id` may be absent; `commerce/orders/{id}` returns line items keyed by
 * nothing stable), so the whole record is serialised instead. Distinct rows from
 * the same source shape serialise distinctly, and a key that is ugly in devtools is
 * better than a React duplicate-key warning on every ledger.
 */
export function recordKey(row: unknown): string {
  return typeof row === 'object' && row !== null ? (JSON.stringify(row) ?? '') : String(row);
}

/**
 * The labelled line that discloses a preview instead of hiding behind a state.
 *
 * The text is formatted by the caller so the numbers and the words come from the
 * same translated string. Nothing is rendered when the preview is the whole
 * result, because a disclosure that always appears teaches a reader to skip it.
 */
export function TruncationNote({
  shown,
  total,
  text,
}: {
  shown: number;
  total: number;
  text: string;
}) {
  if (total <= shown) return null;
  return <p className="num text-xs text-ink-soft">{text}</p>;
}
