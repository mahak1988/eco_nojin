import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';

import { ledgerCopy } from '../../../_lib/copy';
import {
  integerSegment,
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../_lib/surface';

const SLUG = 'admin-admin-content-item_id-versions';
const ROUTE = '/admin/content/{item_id}/versions';
const PATH = '/api/v1/admin/content/{item_id}/versions';

/**
 * `GET /api/v1/admin/content/{item_id}/versions` —
 * `services/api_gateway/routers/admin_content.py:200`.
 *
 * `response_model=List[ContentVersionResponse]`, so the payload is a bare array
 * and there is no envelope key to name. `ContentVersionResponse` is declared at
 * `admin_content.py:50` with `id`, `content_id`, `version`, `title`, `body` and
 * `created_at`. The handler selects `ContentVersion` by `content_id` ordered by
 * descending `version` (`admin_content.py:207-210`), so the rows are persisted
 * records rather than a derived summary.
 *
 * The path parameter is declared `item_id: int`, so a non-numeric segment is a
 * `422` the gateway would answer, not a lookup that could miss. The page reads the
 * segment as a number first and says why it made no request, instead of reporting
 * a validation failure it could have predicted.
 */
interface VersionRow {
  id?: number | string;
  content_id?: number | string;
  version?: number | string;
  title?: string;
  body?: string | null;
  created_at?: string | null;
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: VersionRow[];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  // A parameterised record is not a document address, so it does not advertise a
  // canonical of its own: it points at the collection it belongs to.
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/admin/content`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/admin/content'),
      languages: languageAlternates('/admin/content'),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; item_id: string }>;
}) {
  const { item_id } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');
  const itemId = integerSegment(item_id);
  const endpoint = itemId === null ? PATH : PATH.replace('{item_id}', String(itemId));

  const result: Fetched =
    itemId === null
      ? { ok: false, status: 0 }
      : await adminGet<VersionRow[]>(adminToken(await readAdminSession()), endpoint);

  // No request was made, so there is no result to resolve a state from and no row
  // to count. The page reports `ready` with a labelled notice in the data region:
  // the reader has been told the whole story, and an invented empty state would
  // claim the gateway had answered and found nothing.
  const rows = itemId === null ? [] : readRows<VersionRow>(result.ok ? result.data : undefined);
  const state = itemId === null ? 'ready' : resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      slug={SLUG}
      state={state}
      total={rows.length}
      ok={itemId !== null && result.ok}
      verified={itemId !== null && result.ok && verificationOf(result.data)}
      stateDetail={`${endpoint} · ${rows.length}`}
      data={
        <div className="flex flex-col gap-2">
          {itemId === null ? (
            <p className="text-sm text-copper">
              <span className="num">{item_id || '—'}</span> — {copy.notAnIdentifier}
            </p>
          ) : (
            <LedgerTable<VersionRow>
              columns={[
                { key: 'version', header: c.version, render: (row) => scalar(row.version) },
                { key: 'title', header: c.name, render: (row) => scalar(row.title) },
                { key: 'created', header: c.created, render: (row) => scalar(row.created_at) },
                {
                  key: 'body',
                  header: c.detail,
                  render: (row) => scalar(row.body).slice(0, 160),
                },
              ]}
              rows={visible}
              rowKey={(row) => String(row.id)}
              caption={meta('title')}
              emptyLabel={copy.emptyLabel}
            />
          )}
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
