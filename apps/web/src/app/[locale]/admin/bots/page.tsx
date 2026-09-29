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

const SLUG = 'admin-admin-bots';
const ROUTE = '/admin/bots';
const PATH = '/api/v1/admin/bots';

/**
 * `GET /api/v1/admin/bots` — `services/api_gateway/routers/admin_bots.py:41`.
 *
 * `response_model=List[BotStatusResponse]`, so the payload is a bare array.
 * `BotStatusResponse` is declared at `admin_bots.py:18` with `key`, `name`,
 * `enabled`, `platform`, `status`, `last_activity` and `message_count`.
 *
 * The registry is seeded, not probed: `BOT_REGISTRY` is four literals declared at
 * `admin_bots.py:33-38` under the comment "Mock bot registry (replace with actual
 * bot manager)". A row changes only when `POST /{key}/toggle` or `POST /{key}/restart`
 * mutates the same dict in the same process, and nothing in this process ever
 * writes `last_activity` or `message_count`, so those two fields carry their
 * pydantic defaults rather than a reading. They are therefore not rendered as
 * columns: a `0` and a `null` that no code ever set would read to an operator as
 * "no messages, never active".
 */
interface BotRow {
  key?: string;
  name?: string;
  enabled?: boolean;
  platform?: string;
  status?: string;
  last_activity?: string | null;
  message_count?: number;
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

  const result = await adminGet<BotRow[]>(adminToken(session), PATH);
  const rows = readRows<BotRow>(result.ok ? result.data : undefined);
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
          <LedgerTable<BotRow>
            columns={[
              { key: 'key', header: c.key, render: (row) => scalar(row.key) },
              { key: 'name', header: c.name, render: (row) => scalar(row.name) },
              { key: 'platform', header: c.source, render: (row) => scalar(row.platform) },
              { key: 'enabled', header: c.status, render: (row) => (row.enabled ? '✓' : '—') },
              { key: 'state', header: c.value, render: (row) => scalar(row.status) },
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
          {copy.seededRegistry} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
