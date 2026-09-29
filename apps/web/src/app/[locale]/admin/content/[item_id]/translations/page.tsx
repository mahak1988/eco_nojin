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

const SLUG = 'admin-admin-content-item_id-translations';
const ROUTE = '/admin/content/{item_id}/translations';
const PATH = '/api/v1/admin/content/{item_id}/translations';

/**
 * `GET /api/v1/admin/content/{item_id}/translations` —
 * `services/api_gateway/routers/admin_content.py:213`.
 *
 * `response_model=List[ContentTranslationResponse]`, so the payload is a bare
 * array. `ContentTranslationResponse` is declared at `admin_content.py:61` with
 * `id`, `content_id`, `locale`, `title`, `body`, `source`, `is_published` and
 * `created_at`. The handler selects `ContentTranslation` by `content_id`
 * (`admin_content.py:220-223`), so the rows are persisted translations.
 *
 * The path parameter is `item_id: int`, so a non-numeric segment is a `422` rather
 * than a lookup that could miss. The page reads the segment as a number first and
 * says why it made no request.
 */
interface TranslationRow {
  id?: number | string;
  content_id?: number | string;
  locale?: string;
  title?: string;
  body?: string | null;
  source?: string;
  is_published?: boolean;
  created_at?: string | null;
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: TranslationRow[];
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
      : await adminGet<TranslationRow[]>(adminToken(await readAdminSession()), endpoint);

  const rows = itemId === null ? [] : readRows<TranslationRow>(result.ok ? result.data : undefined);
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
            <LedgerTable<TranslationRow>
              columns={[
                { key: 'locale', header: c.locale, render: (row) => scalar(row.locale) },
                { key: 'title', header: c.name, render: (row) => scalar(row.title) },
                { key: 'source', header: c.source, render: (row) => scalar(row.source) },
                {
                  key: 'published',
                  header: c.status,
                  render: (row) => (row.is_published ? '✓' : '—'),
                },
                { key: 'created', header: c.created, render: (row) => scalar(row.created_at) },
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
