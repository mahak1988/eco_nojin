import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  readRows,
  recordKey,
  resolveLedgerState,
  scalar,
} from '../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-ledger-trial-balance';
const ROUTE = '/workspace/finance/ledger/trial-balance';
const PATH = '/api/v1/finance/ledger/trial-balance';

/**
 * `GET /api/v1/finance/ledger/trial-balance` —
 * `services/finance/routers/finance.py:337`.
 *
 * `response_model=TrialBalanceResponse`, declared at `finance.py:323` with
 * `as_of`, `rows` and `totals`. A row is a `TrialBalanceRow` (`finance.py:307`):
 * `account_id`, `asset`, `debit_balance`, `credit_balance`, `total_debits`,
 * `total_credits`. A total is a `TrialBalanceTotals` (`finance.py:316`): `asset`,
 * `debit`, `credit`, and the boolean `balanced`.
 *
 * Only posted batches are counted, which is what makes a trial balance an auditor's
 * instrument rather than a report of intended entries.
 *
 * ## The upstream gate is stronger than the surface
 *
 * `user: dict = Depends(require_admin)` (`finance.py:342`) admits only
 * administrators, while `WORKSPACE_ROLES` admits management and professional roles
 * too. A reader in a professional role gets a `403`, which the page renders as the
 * `error` state — the honest answer, not something to work around.
 */
interface TrialRow {
  account_id?: string;
  asset?: string;
  debit_balance?: string;
  credit_balance?: string;
  total_debits?: string;
  total_credits?: string;
}

interface TrialTotal {
  asset?: string;
  debit?: string;
  credit?: string;
  balanced?: boolean;
}

interface TrialPayload {
  as_of?: string | null;
  rows?: TrialRow[];
  totals?: TrialTotal[];
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: TrialPayload;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('workspace');

  const result: Fetched = await workspaceGet<TrialPayload>(
    workspaceToken(await readWorkspaceSession()),
    PATH,
  );
  const rows = readRows<TrialRow>(result.ok ? result.data?.rows : undefined);
  const totals = result.ok ? (result.data?.totals ?? []) : [];
  // A trial balance that does not balance is a complete answer that disagrees with
  // itself, so it is a row set and not an error — the `balanced` column is the
  // contract's own verdict and is rendered as data.
  const state = resolveLedgerState(result, rows.length + totals.length);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="workspace"
      title={meta('title')}
      description={meta('description')}
      path={PATH}
      slug={SLUG}
      state={state}
      total={rows.length + totals.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      summary={
        result.ok ? (
          <div className="flex flex-col gap-2">
            <p className="num text-xs text-ink-soft">
              {c.updated} <span className="text-ink">{scalar(result.data?.as_of)}</span>
            </p>
            <LedgerTable<TrialTotal>
              columns={[
                { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
                { key: 'debit', header: c.amount, render: (row) => scalar(row.debit) },
                { key: 'credit', header: c.total, render: (row) => scalar(row.credit) },
                { key: 'balanced', header: c.status, render: (row) => (row.balanced ? '✓' : '—') },
              ]}
              rows={totals}
              rowKey={(row) => String(row.asset ?? '')}
              caption={meta('title')}
              emptyLabel={copy.emptyLabel}
            />
          </div>
        ) : null
      }
      data={
        <LedgerTable<TrialRow>
          columns={[
            { key: 'account', header: c.key, render: (row) => scalar(row.account_id) },
            { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
            { key: 'debit_balance', header: c.amount, render: (row) => scalar(row.debit_balance) },
            { key: 'credit_balance', header: c.total, render: (row) => scalar(row.credit_balance) },
            { key: 'total_debits', header: c.value, render: (row) => scalar(row.total_debits) },
            { key: 'total_credits', header: c.count, render: (row) => scalar(row.total_credits) },
          ]}
          rows={rows}
          rowKey={(row) => recordKey(row)}
          caption={meta('title')}
          emptyLabel={copy.emptyLabel}
        />
      }
    />
  );
}
