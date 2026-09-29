import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

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

const SLUG = 'admin-admin-settings';
const ROUTE = '/admin/settings';
const PATH = '/api/v1/admin/settings';

/**
 * `GET /api/v1/admin/settings` — `services/api_gateway/routers/admin_settings.py:36`.
 *
 * `response_model=List[SettingResponse]`, so the payload is a bare array.
 * `SettingResponse` is declared at `admin_settings.py:16` with `key`, `value`,
 * `description`, `is_secret`, `updated_at` and `updated_by`.
 *
 * Two honest limits on what this page can show.
 *
 * The store is `SETTINGS_STORE = {}` at `admin_settings.py:33`, a module-level
 * dict that is empty on start and holds only what a `PUT /{key}` has written in
 * the current process. A `200` with zero rows is the normal answer, not a sign
 * that settings are missing from a database — the page says so in its `detail`
 * region rather than letting the `empty` state imply a fault.
 *
 * The `value` field is already masked upstream: `admin_settings.py:44` replaces it
 * with `***` whenever the key contains `secret`, `key` or `password`. The page
 * renders what the contract returns and does not try to recover or infer the real
 * value.
 */
interface SettingRow {
  key?: string;
  value?: string;
  description?: string | null;
  is_secret?: boolean;
  updated_at?: string | null;
  updated_by?: string | null;
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

  // The contract's optional `prefix` is not sent, so the response is the whole
  // store rather than a filtered view of it.
  const result = await adminGet<SettingRow[]>(adminToken(await readAdminSession()), PATH);
  const rows = readRows<SettingRow>(result.ok ? result.data : undefined);
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
      stateDetail={`${PATH} · ${rows.length}`}
      data={
        <div className="flex flex-col gap-2">
          <LedgerTable<SettingRow>
            columns={[
              { key: 'key', header: c.key, render: (row) => scalar(row.key) },
              { key: 'value', header: c.value, render: (row) => scalar(row.value) },
              { key: 'description', header: c.detail, render: (row) => scalar(row.description) },
              { key: 'secret', header: c.status, render: (row) => (row.is_secret ? '✓' : '—') },
              { key: 'updated', header: c.updated, render: (row) => scalar(row.updated_at) },
              { key: 'by', header: c.member, render: (row) => scalar(row.updated_by) },
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
          {copy.processMemory} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
