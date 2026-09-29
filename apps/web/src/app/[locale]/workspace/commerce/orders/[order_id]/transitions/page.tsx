import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PREVIEW_LIMIT,
  readRows,
  recordKey,
  resolveLedgerState,
  scalar,
  TruncationNote,
} from '../../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-commerce-orders-order_id-transitions';
const ROUTE = '/workspace/commerce/orders/{order_id}/transitions';
const PATH = '/api/v1/commerce/orders/{order_id}/transitions';

/**
 * `GET /api/v1/commerce/orders/{order_id}/transitions` —
 * `services/commerce/routers/commerce.py:271`, `response_model=list[str]`.
 *
 * The handler loads the order and returns
 * `list(OrderStateMachine.get_allowed_transitions(order.status))`, so the payload
 * is a bare array of state names. It is a derived answer, not a stored list: the
 * same status always yields the same transitions, and the page labels them as the
 * transitions the current status permits rather than as transitions that have
 * happened.
 *
 * ## The upstream gate is weaker than the surface
 *
 * `user=Depends(require_user)` (`commerce.py:274`) with no ownership condition, so
 * any authenticated caller can ask about any order id. `OrderService.get_order`
 * raises through `EcoNojinException` and the handler maps that to a `404`
 * (`commerce.py:99-101`), so an unknown id is an honest miss rather than an empty
 * list — which is why the `empty` state here means "the order exists and permits
 * nothing", not "not found".
 */
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
      url: `${BASE_URL}/${locale}/workspace/commerce/orders`,
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
  params: Promise<{ locale: string; order_id: string }>;
}) {
  const { order_id } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('workspace');
  const endpoint = PATH.replace('{order_id}', encodeURIComponent(order_id));

  const result = await workspaceGet<string[]>(
    workspaceToken(await readWorkspaceSession()),
    endpoint,
  );
  const rows = readRows<string>(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
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
          <LedgerTable<string>
            columns={[{ key: 'transition', header: c.action, render: (row) => scalar(row) }]}
            rows={visible}
            rowKey={(row) => recordKey(row)}
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
          {copy.upstreamGate} <span className="num">{endpoint}</span>
        </p>
      }
    />
  );
}
