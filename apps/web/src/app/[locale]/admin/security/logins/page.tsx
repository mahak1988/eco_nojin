import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../../_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../_lib/surface';

const SLUG = 'admin-admin-security-logins';
const ROUTE = '/admin/security/logins';
const PATH = '/api/v1/admin/security/logins';

/**
 * `GET /api/v1/admin/security/logins` —
 * `services/api_gateway/routers/admin_security.py:43`.
 *
 * `response_model=List[LoginHistoryResponse]`, so the payload is a bare array.
 * `LoginHistoryResponse` is declared at `admin_security.py:60` with `id`, `user_id`,
 * `ip_address`, `user_agent`, `success`, `login_at` and `failure_reason`.
 *
 * ## The contract cannot answer today
 *
 * `admin_security.py:54` imports `LoginHistory` from `database.models`, and no
 * such class is declared there. The import fails when the dependency resolves, so
 * this request returns a server error rather than a row set. The page is built to
 * the contract as declared and renders the `error` state naming the path and the
 * status the gateway returned; the missing model is recorded in the console
 * registry at `admin-sections.ts:300-308` and is a gateway fix, not a page fix.
 *
 * The window is the router's `hours` parameter, defaulting to 24 and not fixed
 * (`admin_security.py:45, 53`), so a row set from this contract is a window and
 * not a lifetime. The page sends no parameter and therefore shows the default.
 */
interface LoginRow {
  id?: number | string;
  user_id?: string | null;
  ip_address?: string;
  user_agent?: string;
  success?: boolean;
  login_at?: string;
  failure_reason?: string | null;
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
      url: `${BASE_URL}/${locale}/admin/security`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/admin/security'),
      languages: languageAlternates('/admin/security'),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');

  const result = await adminGet<LoginRow[]>(adminToken(await readAdminSession()), PATH);
  const rows = readRows<LoginRow>(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={PATH}
      slug={SLUG}
      state={state}
      total={rows.length}
      ok={result.ok}
      stateDetail={result.ok ? `${PATH} · ${rows.length}` : `${PATH} · ${result.status}`}
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<LoginRow>
            columns={[
              { key: 'login_at', header: c.created, render: (row) => scalar(row.login_at) },
              { key: 'user', header: c.member, render: (row) => scalar(row.user_id) },
              { key: 'ip', header: c.source, render: (row) => scalar(row.ip_address) },
              { key: 'agent', header: c.detail, render: (row) => scalar(row.user_agent) },
              { key: 'success', header: c.status, render: (row) => (row.success ? '✓' : '—') },
              { key: 'reason', header: c.message, render: (row) => scalar(row.failure_reason) },
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
    />
  );
}
