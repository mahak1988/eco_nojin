import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-accounts';
const ROUTE = '/workspace/finance/accounts';
const PATH = '/api/v1/finance/accounts';

/**
 * `GET /api/v1/finance/accounts` — `services/finance/routers/finance.py:136`.
 *
 * `response_model=List[AccountResponse]`, so the payload is a bare array.
 * `AccountResponse` is declared at `finance.py:105` with `id`, `code`, `name`,
 * `type`, `asset`, `currency` and `is_active`.
 *
 * `is_active` defaults to `True` (`finance.py:139`) and the filter is applied at
 * `finance.py:146-147`, so this is the active chart of accounts; an archived
 * account is not in the response and the page does not imply that it is.
 *
 * ## The upstream gate is weaker than the surface
 *
 * The handler's only identity dependency is `user: dict = Depends(require_user)`
 * (`finance.py:141`), so the gateway applies no role gate beyond "an authenticated
 * session exists" and returns the whole chart of accounts to any of them. The
 * route sits inside the workspace shell, which refuses any role outside its
 * allowlist, and that shell is where the access decision is actually made — but
 * `lib/workspaces/guard.ts` says itself that a frontend gate is not an
 * authorization authority. So the page states the upstream gate beside the rows
 * rather than implying the contract enforces it.
 */
interface AccountRow {
  id?: number | string;
  code?: string;
  name?: string;
  type?: string;
  asset?: string | null;
  currency?: string;
  is_active?: boolean;
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
  const session = await readWorkspaceSession();

  const result = await workspaceGet<AccountRow[]>(workspaceToken(session), PATH);
  const rows = readRows<AccountRow>(result.ok ? result.data : undefined);
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
          <LedgerTable<AccountRow>
            columns={[
              { key: 'code', header: c.key, render: (row) => scalar(row.code) },
              { key: 'name', header: c.name, render: (row) => scalar(row.name) },
              { key: 'type', header: c.type, render: (row) => scalar(row.type) },
              { key: 'asset', header: c.group, render: (row) => scalar(row.asset) },
              { key: 'currency', header: c.currency, render: (row) => scalar(row.currency) },
              { key: 'active', header: c.status, render: (row) => (row.is_active ? '✓' : '—') },
            ]}
            rows={visible}
            rowKey={(row) => String(row.id)}
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
