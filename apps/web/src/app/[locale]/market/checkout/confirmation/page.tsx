'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
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
  getOrder,
  ORDERS_SOURCE,
  type OrderListEntry,
} from '@/lib/api/cart';
import {
  ESCROW_SOURCE,
  type EscrowStatusResponse,
  getEscrowStatus,
  heldAmount,
} from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function CheckoutConfirmationPage() {
  const checkout = useTranslations('market.checkout');
  const escrow = useTranslations('market.escrow');
  const product = useTranslations('market.product');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const orderId = searchParams.get('order') ?? '';
  const paymentId = searchParams.get('payment') ?? '';

  const [order, setOrder] = useState<OrderListEntry | null>(null);
  const [ledger, setLedger] = useState<EscrowStatusResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const source = paymentId
    ? `${ESCROW_SOURCE}/${encodeURIComponent(paymentId)}/escrow`
    : orderId
      ? ORDERS_SOURCE
      : ESCROW_SOURCE;

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    if (!orderId && !paymentId) {
      setOrder(null);
      setLedger(null);
      setDataState('unavailable');
      return;
    }
    if (orderId) {
      const orderResult = await getOrder(orderId);
      if (!orderResult.ok) {
        const kind = classifyApiFailure(orderResult.status);
        setFailureKind(kind);
        setDetail(orderResult.error);
        setOrder(null);
        setDataState(
          kind === 'offline'
            ? 'offline'
            : kind === 'auth'
              ? 'unauthenticated'
              : kind === 'not-found'
                ? 'unavailable'
                : 'error',
        );
        return;
      }
      setOrder(orderResult.data);
    }
    if (paymentId) {
      const escrowResult = await getEscrowStatus(paymentId);
      if (!escrowResult.ok) {
        const kind = classifyApiFailure(escrowResult.status);
        setFailureKind(kind);
        setDetail(escrowResult.error);
        setLedger(null);
        setDataState(
          kind === 'offline'
            ? 'offline'
            : kind === 'auth'
              ? 'unauthenticated'
              : kind === 'not-found'
                ? 'unavailable'
                : 'error',
        );
        return;
      }
      setLedger(escrowResult.data);
    }
    setDataState('live');
  }, [orderId, paymentId]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setOrder(null);
      setLedger(null);
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

  const held = ledger ? heldAmount(ledger.entries) : null;

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/checkout`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {common('back')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {checkout('confirmation')}
            </h1>
            <ProvenanceStamp
              source={source}
              label={escrow('escrowProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        {dataState !== 'live' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' || dataState === 'unavailable' ? detail : undefined}
            failureKind={failureKind}
            onRetry={orderId || paymentId ? () => void load() : undefined}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {checkout('cartReview')}
              </Button>
            }
          />
        )}

        {dataState === 'live' && (
          <div className="space-y-6">
            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{checkout('orderPlaced')}</h2>
              <dl className="space-y-2">
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('orderId')}</dt>
                  <dd className="num break-all font-mono text-end text-sm text-ink">
                    {order?.id ?? orderId ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{product('productSpecs')}</dt>
                  <dd className="text-end text-sm text-ink">
                    {order?.product_name ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{product('status')}</dt>
                  <dd>{order ? <StatusDot state="warn" label={order.status} /> : null}</dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-line pt-2">
                  <dt className="font-medium text-ink">{common('total')}</dt>
                  <dd className="num text-lg font-bold text-forest">
                    {order ? formatPrice(order.total_price) : statusLine('unavailable')}
                  </dd>
                </div>
              </dl>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{checkout('escrowStatus')}</h2>
              {ledger ? (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="num font-mono text-xs text-ink-soft">{ledger.payment_id}</p>
                    <StatusDot
                      state={ledger.escrow_status === 'held' ? 'ok' : 'warn'}
                      label={`${ledger.payment_status} · ${ledger.escrow_status}`}
                    />
                  </div>
                  <ul className="mt-4 space-y-2">
                    {ledger.entries.map((entry) => (
                      <li key={entry.id} className="flex justify-between gap-3 text-sm">
                        <span className="num font-mono text-xs text-ink-soft">
                          {entry.entry_type}
                        </span>
                        <span className="num text-ink">
                          {entry.amount === null
                            ? statusLine('unavailable')
                            : formatPrice(entry.amount)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              )}
              <p className="mt-4 text-sm text-ink-soft">
                {escrow('amount')}: {held === null ? statusLine('unavailable') : formatPrice(held)}
              </p>
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/orders`)}>
                {checkout('viewOrders')}
              </Button>
              {order ? (
                <Button
                  variant="secondary"
                  onClick={() => router.push(`/${locale}/market/orders/${order.id}/timeline`)}
                >
                  {escrow('eventTimeline')}
                </Button>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
