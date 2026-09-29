import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../admin/_lib/copy';
import { LedgerSurface, RecordList, resolveLedgerState, scalar } from '../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-wallet';
const ROUTE = '/workspace/finance/wallet';
const PATH = '/api/v1/finance/wallet';

/**
 * `GET /api/v1/finance/wallet` — `services/finance/routers/finance.py:411`.
 *
 * `response_model=WalletBalanceResponse`, so the payload is one record.
 * `WalletBalanceResponse` is declared at `finance.py:70` with `user_id`,
 * `balance`, `total_earned`, `total_redeemed` and `is_active`. The three money
 * fields are `Decimal`, so they are rendered as text and never re-summed here.
 *
 * ## This is the one record on this surface that is genuinely personal
 *
 * `finance.py:417-419` reads the wallet state for the caller's own id, so unlike
 * the ledger routes on this surface the contract scopes the data to the reader. The
 * upstream gate is still `require_user` (`finance.py:414`) with no role check, and
 * the page says so rather than letting the scoping imply a stronger gate than the
 * one that exists.
 */
interface WalletPayload {
  user_id?: string;
  balance?: string;
  total_earned?: string;
  total_redeemed?: string;
  is_active?: boolean;
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: WalletPayload;
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

  const result: Fetched = await workspaceGet<WalletPayload>(
    workspaceToken(await readWorkspaceSession()),
    PATH,
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
      path={PATH}
      slug={SLUG}
      state={state}
      total={rows.length}
      ok={result.ok}
      data={
        result.ok && result.data ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.member, value: scalar(result.data.user_id) },
              { label: c.value, value: scalar(result.data.balance) },
              { label: c.amount, value: scalar(result.data.total_earned) },
              { label: c.total, value: scalar(result.data.total_redeemed) },
              { label: c.status, value: result.data.is_active ? '✓' : '—' },
            ]}
          />
        ) : null
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.upstreamGate} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
