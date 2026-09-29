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
  PREVIEW_LIMIT,
  readRows,
  recordKey,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-ledger-entries';
const ROUTE = '/workspace/finance/ledger/entries';
const PATH = '/api/v1/finance/ledger/entries';

/**
 * `GET /api/v1/finance/ledger/entries` — `services/finance/routers/finance.py:281`.
 *
 * The handler declares no `response_model` and returns a list of `dict`s built from
 * the journal entry (`finance.py:292-304`): `id`, `batch_id`, `account_id`,
 * `entry_type`, `asset`, `amount`, `description` and `created_at`. The amount is
 * stringified upstream, so it is rendered as text and never summed or re-parsed
 * here.
 *
 * ## The upstream gate is weaker than the surface
 *
 * `user: dict = Depends(require_user)` (`finance.py:288`) and no tenant condition
 * reaches the query, which is built from `account_id` and `asset` alone
 * (`finance.py:291`). Every authenticated caller who can reach this route reads
 * every journal entry. The page says so beside the rows instead of implying the
 * rows are scoped to the reader.
 *
 * Two declared parameters are not sent. `batch_id` is accepted at `finance.py:284`
 * and then never used — the service call at `:291` passes only `account_id`,
 * `asset` and `limit`, so filtering by batch would silently do nothing. `limit`
 * defaults to 100, so the response is at most 100 rows whatever the table holds.
 */
interface EntryRow {
  id?: number | string;
  batch_id?: number | string;
  account_id?: string;
  entry_type?: string;
  asset?: string;
  amount?: string;
  description?: string | null;
  created_at?: string | null;
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

  const result = await workspaceGet<EntryRow[]>(workspaceToken(await readWorkspaceSession()), PATH);
  const rows = readRows<EntryRow>(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
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
      total={rows.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<EntryRow>
            columns={[
              { key: 'id', header: c.identifier, render: (row) => scalar(row.id) },
              { key: 'created', header: c.created, render: (row) => scalar(row.created_at) },
              { key: 'account', header: c.key, render: (row) => scalar(row.account_id) },
              { key: 'type', header: c.type, render: (row) => scalar(row.entry_type) },
              { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
              { key: 'amount', header: c.amount, render: (row) => scalar(row.amount) },
              { key: 'batch', header: c.version, render: (row) => scalar(row.batch_id) },
              { key: 'description', header: c.detail, render: (row) => scalar(row.description) },
            ]}
            rows={visible}
            rowKey={(row) => recordKey(row)}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
          <TruncationNote
            shown={visible.length}
            total={rows.length}
            text={copy.t('showing', { shown: visible.length, total: rows.length })}
          />
        </div>
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.upstreamGate} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
