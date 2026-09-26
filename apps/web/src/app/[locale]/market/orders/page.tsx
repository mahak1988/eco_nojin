'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import {
  type ApiFailureKind,
  classifyApiFailure,
  listOrders,
  ORDER_STATUSES,
  ORDERS_SOURCE,
  type OrderListEntry,
  type OrderStatus,
} from '@/lib/api/cart';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

const CLOSED_STATUSES: ReadonlySet<string> = new Set(['delivered', 'cancelled']);

function orderDot(status: string): 'ok' | 'warn' | 'down' {
  if (status === 'cancelled') return 'down';
  if (status === 'delivered') return 'ok';
  return 'warn';
}

export default function OrdersPage() {
  const checkout = useTranslations('market.checkout');
  const escrow = useTranslations('market.escrow');
  const product = useTranslations('market.product');
  const market = useTranslations('market');
  const template = useTranslations('market.template');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [orders, setOrders] = useState<OrderListEntry[]>([]);
  const [status, setStatus] = useState<OrderStatus | ''>('');
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await listOrders(status === '' ? undefined : status);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setOrders([]);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setOrders(result.data.orders);
    setDataState(result.data.orders.length > 0 ? 'live' : 'empty');
  }, [status]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setOrders([]);
      setDataState('unauthenticated');
      return;
    }
    setDataState('loading');
    void load();
  }, [authLoading, user, load]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (online) void load();
    });
  }, [dataState, load]);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const formatDateTime = (value: string) => {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime())
      ? value
      : new Intl.DateTimeFormat(locale === 'fa' ? 'fa-IR' : 'en-GB', {
          dateStyle: 'medium',
          timeStyle: 'short',
        }).format(parsed);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {nav('market')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {checkout('viewOrders')}
            </h1>
            <ProvenanceStamp
              source={ORDERS_SOURCE}
              label={template('source')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        <div className="mb-6 flex flex-wrap items-end gap-3">
          <div>
            <label htmlFor="order-status" className="mb-1 block text-sm text-ink-soft">
              {product('status')}
            </label>
            <select
              id="order-status"
              value={status}
              onChange={(event) => {
                const next = event.target.value;
                setStatus(next === '' ? '' : (next as OrderStatus));
              }}
              className="rounded border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value="">{product('status')}</option>
              {ORDER_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
        </div>

        {dataState === 'loading' && <MarketDataStateNotice state="loading" locale={locale} />}

        {dataState !== 'live' && dataState !== 'loading' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={market('empty')}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market`)}>
                {nav('market')}
              </Button>
            }
          />
        )}

        {dataState === 'live' && (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} density="compact">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="font-medium text-ink">{order.product_name}</h2>
                    <p className="num mt-1 font-mono text-xs text-ink-soft">
                      {escrow('orderId')}: {order.id}
                    </p>
                    <time
                      className="num mt-1 block text-xs text-ink-soft"
                      dateTime={order.created_at}
                    >
                      {formatDateTime(order.created_at)}
                    </time>
                  </div>
                  <StatusDot state={orderDot(order.status)} label={order.status} />
                </div>

                <dl className="mt-4 space-y-2">
                  <div className="flex justify-between gap-4">
                    <dt className="text-sm text-ink-soft">{escrow('buyer')}</dt>
                    <dd className="text-sm text-ink">{order.buyer_name}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-sm text-ink-soft">{escrow('seller')}</dt>
                    <dd className="num break-all text-end text-sm text-ink">
                      {order.seller_id || statusLine('unavailable')}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-sm text-ink-soft">{product('quantity')}</dt>
                    <dd className="num text-sm text-ink">{order.quantity_kg}</dd>
                  </div>
                  <div className="flex justify-between gap-4 border-t border-line pt-2">
                    <dt className="font-medium text-ink">{common('total')}</dt>
                    <dd className="num font-medium text-forest">
                      {formatPrice(order.total_price)}
                    </dd>
                  </div>
                </dl>

                <div className="mt-4 flex flex-wrap gap-3">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => router.push(`/${locale}/market/orders/${order.id}/timeline`)}
                  >
                    {escrow('eventTimeline')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/${locale}/market/orders/${order.id}/tracking`)}
                  >
                    {product('status')}
                  </Button>
                  {CLOSED_STATUSES.has(order.status) ? null : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/${locale}/market/orders/${order.id}/dispute`)}
                    >
                      {escrow('openDispute')}
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
