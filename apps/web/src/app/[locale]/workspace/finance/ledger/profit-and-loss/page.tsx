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
  recordKey,
  resolveLedgerState,
  scalar,
} from '../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-ledger-profit-and-loss';
const ROUTE = '/workspace/finance/ledger/profit-and-loss';
const PATH = '/api/v1/finance/ledger/profit-and-loss';

/**
 * `GET /api/v1/finance/ledger/profit-and-loss` —
 * `services/finance/routers/finance.py:388`.
 *
 * `response_model=ProfitAndLossResponse`, declared at `finance.py:378` with
 * `from_date`, `to_date`, `asset`, `income`, `expense`, `unclassified` and
 * `totals`. A line is a `ProfitAndLossLine` (`finance.py:361`): `account_id`,
 * `account_code`, `account_name`, `asset`, `amount` — the amount stringified. A
 * total is a `ProfitAndLossTotals` (`finance.py:370`): `asset`, `income`,
 * `expense`, `net` and the boolean `profitable`.
 *
 * `unclassified` holds accounts that entries reference but the chart of accounts
 * does not define, surfaced rather than dropped (`finance.py:384-385`). The page
 * renders that list rather than hiding it, because a statement that quietly omits
 * money it cannot classify is the failure this endpoint was written to prevent.
 *
 * ## The upstream gate is stronger than the surface
 *
 * `user: dict = Depends(require_admin)` (`finance.py:393`) admits only
 * administrators; `WORKSPACE_ROLES` admits management and professional roles too,
 * so a reader in a professional role gets a `403`, rendered as the `error` state.
 */
interface Line {
  account_id?: string;
  account_code?: string | null;
  account_name?: string | null;
  asset?: string;
  amount?: string;
}

interface Total {
  asset?: string;
  income?: string;
  expense?: string;
  net?: string;
  profitable?: boolean;
}

interface Payload {
  from_date?: string | null;
  to_date?: string | null;
  asset?: string | null;
  income?: Line[];
  expense?: Line[];
  unclassified?: Record<string, unknown>[];
  totals?: Total[];
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: Payload;
}

const LINE_COLUMNS = (
  c: Awaited<ReturnType<typeof ledgerCopy>>['columns'],
): { key: string; header: string; render: (row: Line) => string }[] => [
  { key: 'code', header: c.key, render: (row) => scalar(row.account_code) },
  { key: 'name', header: c.name, render: (row) => scalar(row.account_name) },
  { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
  { key: 'amount', header: c.amount, render: (row) => scalar(row.amount) },
];

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

  const result: Fetched = await workspaceGet<Payload>(
    workspaceToken(await readWorkspaceSession()),
    PATH,
  );
  const income = result.ok ? (result.data?.income ?? []) : [];
  const expense = result.ok ? (result.data?.expense ?? []) : [];
  const unclassified = result.ok ? (result.data?.unclassified ?? []) : [];
  const totals = result.ok ? (result.data?.totals ?? []) : [];
  const state = resolveLedgerState(
    result,
    income.length + expense.length + unclassified.length + totals.length,
  );
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
      total={income.length + expense.length + unclassified.length + totals.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      summary={
        result.ok ? (
          <div className="flex flex-col gap-2">
            <p className="num text-xs text-ink-soft">
              {c.created} <span className="text-ink">{scalar(result.data?.from_date)}</span> —{' '}
              <span className="text-ink">{scalar(result.data?.to_date)}</span>
            </p>
            <LedgerTable<Total>
              columns={[
                { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
                { key: 'income', header: c.value, render: (row) => scalar(row.income) },
                { key: 'expense', header: c.amount, render: (row) => scalar(row.expense) },
                { key: 'net', header: c.total, render: (row) => scalar(row.net) },
                {
                  key: 'profitable',
                  header: c.status,
                  render: (row) => (row.profitable ? '✓' : '—'),
                },
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
        <div className="flex flex-col gap-3">
          <LedgerTable<Line>
            columns={LINE_COLUMNS(c)}
            rows={income}
            rowKey={(row) => recordKey(row)}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
          <LedgerTable<Line>
            columns={LINE_COLUMNS(c)}
            rows={expense}
            rowKey={(row) => recordKey(row)}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
          {unclassified.length > 0 ? (
            <LedgerTable<Record<string, unknown>>
              columns={[{ key: 'entry', header: c.detail, render: (row) => scalar(row) }]}
              rows={unclassified}
              rowKey={(row) => recordKey(row)}
              caption={meta('title')}
              emptyLabel={copy.emptyLabel}
            />
          ) : null}
        </div>
      }
      detail={
        <p className="num text-xs text-ink-faint">
          {c.type} <span className="text-ink">{scalar(result.data?.asset)}</span>
        </p>
      }
    />
  );
}
