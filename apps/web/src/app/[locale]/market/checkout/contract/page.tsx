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

export default function CheckoutContractPage() {
  const checkout = useTranslations('market.checkout');
  const escrow = useTranslations('market.escrow');
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
  const [accepted, setAccepted] = useState(false);
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
  const contractHash = ledger?.entries[0]?.id ?? null;

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/checkout/cart-review`)}
              className="text-ink-soft underline hover:text-ink"
            >
              {checkout('cartReview')}
            </button>
            <span aria-hidden="true" className="text-ink-soft">
              /
            </span>
            <span className="text-ink-soft">{checkout('contractAcceptance')}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{escrow('title')}</h1>
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
              <dl className="space-y-2">
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('orderId')}</dt>
                  <dd className="num break-all font-mono text-end text-sm text-ink">
                    {order?.id ?? orderId ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('buyer')}</dt>
                  <dd className="text-end text-sm text-ink">
                    {order?.buyer_name ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('seller')}</dt>
                  <dd className="num break-all text-end text-sm text-ink">
                    {order?.seller_id || statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('contractHash')}</dt>
                  <dd className="num break-all text-end font-mono text-xs text-forest">
                    {contractHash ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-line pt-2">
                  <dt className="font-medium text-ink">{escrow('amount')}</dt>
                  <dd className="num text-lg font-bold text-forest">
                    {order
                      ? formatPrice(order.total_price)
                      : held === null
                        ? statusLine('unavailable')
                        : formatPrice(held)}
                  </dd>
                </div>
              </dl>
            </Card>

            <Card density="compact">
              <h2 className="mb-3 font-medium text-ink">{escrow('parties')}</h2>
              <p role="status" className="text-sm text-ink-soft">
                {statusLine('unavailable')}
              </p>
            </Card>

            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                aria-label={checkout('contractAcceptance')}
                checked={accepted}
                onChange={(event) => setAccepted(event.target.checked)}
                className="mt-1 h-4 w-4"
              />
              <span className="text-sm text-ink-soft">{checkout('contractAcceptance')}</span>
              <StatusDot
                state={accepted ? 'ok' : 'warn'}
                label={accepted ? escrow('signed') : escrow('notSigned')}
              />
            </label>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {common('back')}
              </Button>
              {orderId ? (
                <Button
                  variant="primary"
                  disabled={!accepted}
                  onClick={() => {
                    const payment = paymentId ? `&payment=${encodeURIComponent(paymentId)}` : '';
                    router.push(
                      `/${locale}/market/checkout/escrow-setup?order=${encodeURIComponent(orderId)}${payment}`,
                    );
                  }}
                >
                  {checkout('escrowSetup')}
                </Button>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
