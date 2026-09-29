import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';

import { ledgerCopy } from '../_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../_lib/surface';

const SLUG = 'admin-admin-errors';
const ROUTE = '/admin/errors';
const PATH = '/api/v1/admin/errors';

/**
 * `GET /api/v1/admin/errors` — `services/api_gateway/routers/admin_errors.py:61`.
 *
 * `response_model=List[ErrorResponse]`, so the payload is a bare array and there
 * is no envelope key to name. `ErrorResponse` is declared at `admin_errors.py:27`
 * with `id`, `timestamp`, `severity`, `error_type`, `message`, `endpoint` and
 * `user_id`. The router takes `severity`, `error_type`, `limit` and `offset`
 * (`admin_errors.py:62-65`).
 *
 * The rows are real in-process records: `add_error` feeds the list and the router
 * derives from it. They are not durable — `ERROR_STORE` is a module-level list
 * (`admin_errors.py:38`) and every record is lost on a gateway restart — so the
 * page says so rather than implying a durable incident log.
 */
interface ErrorRow {
  id?: string;
  timestamp?: string;
  severity?: string;
  error_type?: string;
  message?: string;
  endpoint?: string;
  user_id?: string | null;
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
  const copy = await ledgerCopy('admin');
  const session = await readAdminSession();
  const token = adminToken(session);

  // `adminGet` takes a path, so the contract's optional `severity`, `error_type`,
  // `limit` and `offset` are not sent. That is stated in the `detail` region
  // rather than hidden, because a reader who assumes a filter is applied is worse
  // off than one who knows the response is the unfiltered index.
  const result = await adminGet<ErrorRow[]>(token, PATH);
  const rows = readRows<ErrorRow>(result.ok ? result.data : undefined);
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
      verified={result.ok && verificationOf(result.data)}
      stateDetail={`${PATH} · ${rows.length}`}
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<ErrorRow>
            columns={[
              { key: 'id', header: c.identifier, render: (row) => scalar(row.id) },
              { key: 'timestamp', header: c.created, render: (row) => scalar(row.timestamp) },
              { key: 'severity', header: c.status, render: (row) => scalar(row.severity) },
              { key: 'error_type', header: c.type, render: (row) => scalar(row.error_type) },
              { key: 'endpoint', header: c.source, render: (row) => scalar(row.endpoint) },
              { key: 'message', header: c.message, render: (row) => scalar(row.message) },
            ]}
            rows={visible}
            rowKey={(row) => String(row.id ?? '')}
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
          {copy.processMemory} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
