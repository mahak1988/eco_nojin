import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../../admin/_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  RecordList,
  recordKey,
  resolveLedgerState,
  scalar,
} from '../../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-commerce-orders-order_id';
const ROUTE = '/workspace/commerce/orders/{order_id}';
const PATH = '/api/v1/commerce/orders/{order_id}';

/**
 * `GET /api/v1/commerce/orders/{order_id}` — `services/commerce/routers/commerce.py:97`,
 * `response_model=dict`.
 *
 * The handler composes three things into one object (`commerce.py:110-142`): the
 * order row itself (`order_id`, `order_number`, `buyer_id`, `status`,
 * `payment_status`, `subtotal`, `platform_fee`, `landscape_fee`, `total`,
 * `currency`, `tracking_code`, `paid_at`, `shipped_at`, `delivered_at`,
 * `created_at`), its `items`, its `payments`, and `allowed_transitions` — the
 * transitions the current status permits, derived from the state machine rather
 * than stored. Every money field is stringified upstream.
 *
 * ## The upstream gate is weaker than the surface
 *
 * `user=Depends(require_user)` (`commerce.py:98`) with no ownership condition: any
 * authenticated caller can read any order, including another buyer's line items and
 * payment intents. `OrderService.get_order` raises through `EcoNojinException`,
 * mapped to `404` at `commerce.py:99-101`.
 */
interface OrderPayload {
  order_id?: string;
  order_number?: string;
  buyer_id?: string;
  status?: string;
  payment_status?: string;
  subtotal?: string;
  platform_fee?: string;
  landscape_fee?: string;
  total?: string;
  currency?: string;
  tracking_code?: string | null;
  paid_at?: string | null;
  shipped_at?: string | null;
  delivered_at?: string | null;
  created_at?: string;
  items?: {
    id?: string;
    sku_code?: string;
    name?: string;
    quantity?: string;
    unit_price?: string;
    fulfilled_qty?: string;
  }[];
  payments?: { id?: string; provider?: string; amount?: string; status?: string }[];
  allowed_transitions?: string[];
}

interface Fetched {
  ok: boolean;
  status: number;
  data?: OrderPayload;
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
      url: `${BASE_URL}/${locale}/workspace/finance/ledger/entries`,
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

  const result: Fetched = await workspaceGet<OrderPayload>(
    workspaceToken(await readWorkspaceSession()),
    endpoint,
  );
  const order = result.ok ? (result.data ?? {}) : {};
  const items = order.items ?? [];
  const payments = order.payments ?? [];
  const transitions = order.allowed_transitions ?? [];
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
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
      total={result.ok ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      summary={
        result.ok ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.key, value: scalar(order.order_number) },
              { label: c.member, value: scalar(order.buyer_id) },
              { label: c.status, value: scalar(order.status) },
              { label: c.value, value: scalar(order.payment_status) },
              { label: c.currency, value: scalar(order.currency) },
              { label: c.amount, value: scalar(order.total) },
            ]}
          />
        ) : null
      }
      data={
        result.ok ? (
          <div className="flex flex-col gap-3">
            <RecordList
              caption={meta('title')}
              fields={[
                { label: c.count, value: scalar(order.subtotal) },
                { label: c.group, value: scalar(order.platform_fee) },
                { label: c.total, value: scalar(order.landscape_fee) },
                { label: c.source, value: scalar(order.tracking_code) },
                { label: c.created, value: scalar(order.created_at) },
                { label: c.updated, value: scalar(order.paid_at) },
                { label: c.version, value: scalar(order.shipped_at) },
                { label: c.type, value: scalar(order.delivered_at) },
              ]}
            />
            <LedgerTable<NonNullable<OrderPayload['items']>[number]>
              columns={[
                { key: 'sku', header: c.key, render: (row) => scalar(row.sku_code) },
                { key: 'name', header: c.name, render: (row) => scalar(row.name) },
                { key: 'quantity', header: c.count, render: (row) => scalar(row.quantity) },
                { key: 'unit_price', header: c.value, render: (row) => scalar(row.unit_price) },
                { key: 'fulfilled', header: c.status, render: (row) => scalar(row.fulfilled_qty) },
              ]}
              rows={items}
              rowKey={(row) => recordKey(row)}
              caption={meta('title')}
              emptyLabel={copy.emptyLabel}
            />
            <LedgerTable<NonNullable<OrderPayload['payments']>[number]>
              columns={[
                { key: 'provider', header: c.source, render: (row) => scalar(row.provider) },
                { key: 'amount', header: c.amount, render: (row) => scalar(row.amount) },
                { key: 'status', header: c.status, render: (row) => scalar(row.status) },
              ]}
              rows={payments}
              rowKey={(row) => recordKey(row)}
              caption={meta('title')}
              emptyLabel={copy.emptyLabel}
            />
          </div>
        ) : null
      }
      detail={
        <div className="flex flex-col gap-2 text-xs text-ink-soft">
          <p className="num">
            {c.action} · {transitions.length > 0 ? transitions.join(' · ') : '—'}
          </p>
          <p>
            {copy.upstreamGate} <span className="num">{endpoint}</span>
          </p>
        </div>
      }
    />
  );
}
