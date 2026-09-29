import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-finance-idempotency-keys';
const ROUTE = '/workspace/finance/idempotency/keys';
const PATH = '/api/v1/finance/idempotency/keys';

/**
 * `GET /api/v1/finance/idempotency/keys` — `services/finance/routers/finance.py:550`.
 *
 * The handler declares no `response_model` and returns a list of `dict`s built from
 * the `FinIdempotencyKey` row (`finance.py:566-577`), so the published schema is a
 * bare array of untyped objects with `key`, `user_id`, `route`, `status`,
 * `request_hash`, `response_code`, `created_at` and `expires_at`.
 *
 * ## The upstream gate is stronger than the surface
 *
 * `user: dict = Depends(require_admin)` (`finance.py:556`) means the gateway admits
 * only administrators, while `WORKSPACE_ROLES` admits management and professional
 * roles as well. A reader who reaches this page in a professional role gets a `403`
 * from the gateway, which the page renders as the `error` state. That is the honest
 * answer and it is not worked around — the alternative would be for the page to
 * imply a report exists for a reader who may not have it.
 *
 * The `user_id` filter is optional and the page sends it nowhere, so this is every
 * caller's key, not the reader's own. `request_hash` is rendered truncated: a digest
 * does not belong in a table cell in full.
 */
interface KeyRow {
  key?: string;
  user_id?: string;
  route?: string;
  status?: string;
  request_hash?: string;
  response_code?: number;
  created_at?: string | null;
  expires_at?: string | null;
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

  const result = await workspaceGet<KeyRow[]>(workspaceToken(await readWorkspaceSession()), PATH);
  const rows = readRows<KeyRow>(result.ok ? result.data : undefined);
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
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<KeyRow>
            columns={[
              { key: 'key', header: c.key, render: (row) => scalar(row.key) },
              { key: 'user', header: c.member, render: (row) => scalar(row.user_id) },
              { key: 'route', header: c.source, render: (row) => scalar(row.route) },
              { key: 'status', header: c.status, render: (row) => scalar(row.status) },
              {
                key: 'hash',
                header: c.key,
                render: (row) => scalar(row.request_hash).slice(0, 24),
              },
              { key: 'code', header: c.code, render: (row) => scalar(row.response_code) },
              { key: 'created', header: c.created, render: (row) => scalar(row.created_at) },
              { key: 'expires', header: c.updated, render: (row) => scalar(row.expires_at) },
            ]}
            rows={visible}
            rowKey={(row) => String(row.key ?? '')}
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
