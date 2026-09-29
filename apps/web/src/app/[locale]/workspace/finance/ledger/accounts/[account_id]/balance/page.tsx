import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-ledger-accounts-account_id-balance';
const ROUTE = '/workspace/finance/ledger/accounts/{account_id}/balance';
const PATH = '/api/v1/finance/ledger/accounts/{account_id}/balance';

/**
 * `GET /api/v1/finance/ledger/accounts/{account_id}/balance` —
 * `services/finance/routers/finance.py:268`.
 *
 * `response_model=dict`, and the handler returns exactly three keys
 * (`finance.py:278`): `account_id`, `asset` and `balance`, with the balance
 * stringified. `asset` is a query parameter defaulting to `"ECO"`
 * (`finance.py:271`), so the returned asset is the one asked for and not a
 * discovered one.
 *
 * ## The upstream gate is weaker than the surface
 *
 * `user: dict = Depends(require_user)` (`finance.py:274`) with no ownership
 * condition: any authenticated caller can read any account's balance by id. The
 * page states that beside the value.
 */
interface BalancePayload {
  account_id?: string;
  asset?: string;
  balance?: string;
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: BalancePayload;
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
      url: `${BASE_URL}/${locale}/workspace/finance/ledger/accounts`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/workspace/finance/ledger/entries'),
      languages: languageAlternates('/workspace/finance/ledger/entries'),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; account_id: string }>;
}) {
  const { account_id } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('workspace');
  const endpoint = PATH.replace('{account_id}', encodeURIComponent(account_id));

  const result: Fetched = await workspaceGet<BalancePayload>(
    workspaceToken(await readWorkspaceSession()),
    endpoint,
  );
  const rows = result.ok && result.data ? [result.data] : [];
  const state = resolveLedgerState(result, rows.length);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="workspace"
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      slug={SLUG}
      state={state}
      total={rows.length}
      ok={result.ok}
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<BalancePayload>
            columns={[
              { key: 'account', header: c.key, render: (row) => scalar(row.account_id) },
              { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
              { key: 'balance', header: c.value, render: (row) => scalar(row.balance) },
            ]}
            rows={rows}
            rowKey={(row) => String(row.account_id ?? '')}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
          <TruncationNote
            shown={rows.length}
            total={rows.length}
            text={copy.t('showing', { shown: rows.length, total: rows.length })}
          />
        </div>
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.upstreamGate} <span className="num">{endpoint}</span>
        </p>
      }
    />
  );
}
