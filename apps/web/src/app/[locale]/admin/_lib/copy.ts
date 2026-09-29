import { getTranslations } from 'next-intl/server';

import type { LedgerNamespace } from './surface';

/**
 * The strings these pages introduce, resolved from this subtree's fragment.
 *
 * Every one of them is a new key under `admin.ledger.*` or
 * `workspace.ledger.*`. Nothing here redefines a key the catalogues already own:
 * `admin.title`, `admin.sections.*`, `admin.grid.*`, `workspace.pages.*` and
 * `workspace.leads.*` were written by the console and workspace registries and are
 * read from the catalogue directly, because the fragment merge refuses to
 * overwrite an existing key with a different value and a fragment that disagreed
 * with a hand-edited catalogue would fail the merge rather than quietly win.
 *
 * The page *headings* come from `pageMeta.<slug>` and not from here, because
 * `scripts/check-page-meta.mjs` requires a heading to resolve through
 * `getTranslations('pageMeta.…')` and greps for the inline dictionary pattern that
 * bypasses it. Both routes to a translated heading are closed; this file carries
 * everything around them.
 *
 * The namespace translator is handed back rather than pre-resolved, because two
 * of these strings take values. A placeholder name that differs between the
 * fragment and the call site is a runtime `MISSING_MESSAGE` in `next-intl`, not a
 * lint warning, so the fragment keeps `{shown}`/`{total}` intact and the page
 * supplies the numbers at the point of use.
 */

export interface ColumnLabels {
  name: string;
  status: string;
  updated: string;
  created: string;
  value: string;
  type: string;
  key: string;
  source: string;
  identifier: string;
  count: string;
  total: string;
  amount: string;
  detail: string;
  locale: string;
  version: string;
  group: string;
  member: string;
  action: string;
  message: string;
  code: string;
  currency: string;
}

export type LedgerTranslator = (
  key: string,
  values?: Record<string, string | number | Date>,
) => string;

export interface LedgerCopy {
  /**
   * The namespace translator, for `showing` and any string added later that takes
   * values. It is handed back rather than pre-resolved so a placeholder name
   * mismatch is a visible literal at the call site rather than a silently
   * wrong count rendered into a disclosure.
   */
  t: LedgerTranslator;
  columns: ColumnLabels;
  /** The cell text for a field the gateway fills with a constant. */
  notMeasured: string;
  placeholderHeading: string;
  placeholderBody: string;
  /** The disclosure for a contract the gateway gates on authentication alone. */
  upstreamGate: string;
  /** The disclosure for a registry that lives in gateway process memory. */
  processMemory: string;
  /** The disclosure for a registry the gateway seeds rather than probes. */
  seededRegistry: string;
  /** The notice for a path segment the contract's own type rejects. */
  notAnIdentifier: string;
  emptyLabel: string;
}

export async function ledgerCopy(namespace: LedgerNamespace): Promise<LedgerCopy> {
  const t = await getTranslations(`${namespace}.ledger`);

  return {
    t,
    columns: {
      name: t('columns.name'),
      status: t('columns.status'),
      updated: t('columns.updated'),
      created: t('columns.created'),
      value: t('columns.value'),
      type: t('columns.type'),
      key: t('columns.key'),
      source: t('columns.source'),
      identifier: t('columns.identifier'),
      count: t('columns.count'),
      total: t('columns.total'),
      amount: t('columns.amount'),
      detail: t('columns.detail'),
      locale: t('columns.locale'),
      version: t('columns.version'),
      group: t('columns.group'),
      member: t('columns.member'),
      action: t('columns.action'),
      message: t('columns.message'),
      code: t('columns.code'),
      currency: t('columns.currency'),
    },
    notMeasured: t('notMeasured'),
    placeholderHeading: t('placeholderHeading'),
    placeholderBody: t('placeholderBody'),
    upstreamGate: t('upstreamGate'),
    processMemory: t('processMemory'),
    seededRegistry: t('seededRegistry'),
    notAnIdentifier: t('notAnIdentifier'),
    emptyLabel: t('states.empty'),
  };
}
