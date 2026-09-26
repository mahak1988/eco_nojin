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
  type OrderListEntry,
} from '@/lib/api/cart';
import {
  createPayment,
  ESCROW_SOURCE,
  type EscrowStatusResponse,
  getEscrowStatus,
  heldAmount,
  PAYMENT_GATEWAYS,
  type PaymentGateway,
  type PaymentResponse,
} from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function EscrowSetupPage() {
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
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [ledger, setLedger] = useState<EscrowStatusResponse | null>(null);
  const [gateway, setGateway] = useState<PaymentGateway>('bank');
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [acting, setActing] = useState(false);

  const source = paymentId
    ? `${ESCROW_SOURCE}/${encodeURIComponent(paymentId)}/escrow`
    : ESCROW_SOURCE;

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
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
      setDataState(escrowResult.data.entries.length > 0 ? 'live' : 'empty');
      return;
    }
    if (!orderId) {
      setOrder(null);
      setDataState('unavailable');
      return;
    }
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

  /**
   * The amount charged is the server-computed order total, never a value typed
   * on this page, and the request is idempotent.
   */
  const startEscrow = useCallback(async () => {
    if (!user || !order) return;
    setActing(true);
    setDetail('');
    try {
      const result = await createPayment({
        orderId: order.id,
        amount: order.total_price,
        paymentMethod: gateway,
        description: order.product_name,
      });
      if (!result.ok) {
        const kind = classifyApiFailure(result.status);
        setFailureKind(kind);
        setDetail(result.error);
        setPayment(null);
        return;
      }
      setPayment(result.data);
      setLedger(null);
      router.push(
        `/${locale}/market/checkout/escrow-setup?order=${encodeURIComponent(order.id)}&payment=${encodeURIComponent(result.data.id)}`,
      );
    } finally {
      setActing(false);
    }
  }, [user, order, gateway, router, locale]);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const held = ledger ? heldAmount(ledger.entries) : null;

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
            <span className="text-ink-soft">{checkout('escrowSetup')}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {checkout('escrowSetup')}
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
          />
        )}

        {detail && dataState === 'live' ? (
          <p role="alert" className="mb-6 rounded-md bg-clay/10 p-3 text-sm text-clay">
            {detail}
          </p>
        ) : null}

        {dataState === 'live' && order && !payment && (
          <Card density="compact">
            <dl className="space-y-2">
              <div className="flex justify-between gap-4">
                <dt className="text-sm text-ink-soft">{escrow('orderId')}</dt>
                <dd className="num break-all font-mono text-end text-sm text-ink">{order.id}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-sm text-ink-soft">{product('productSpecs')}</dt>
                <dd className="text-end text-sm text-ink">{order.product_name}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-sm text-ink-soft">{product('quantity')}</dt>
                <dd className="num text-sm text-ink">{order.quantity_kg}</dd>
              </div>
              <div className="flex justify-between gap-4 border-t border-line pt-2">
                <dt className="font-medium text-ink">{escrow('amount')}</dt>
                <dd className="num text-lg font-bold text-forest">
                  {formatPrice(order.total_price)}
                </dd>
              </div>
            </dl>

            <fieldset className="mt-6">
              <legend className="mb-2 text-sm text-ink-soft">{checkout('escrowSetup')}</legend>
              <div className="space-y-2">
                {PAYMENT_GATEWAYS.map((option) => (
                  <label key={option} className="flex items-center gap-3 text-sm text-ink">
                    <input
                      type="radio"
                      name="escrow-gateway"
                      checked={gateway === option}
                      onChange={() => setGateway(option)}
                      className="h-4 w-4"
                    />
                    <code className="font-mono">{option}</code>
                  </label>
                ))}
              </div>
            </fieldset>

            <Button
              variant="primary"
              className="mt-6 w-full"
              loading={acting}
              onClick={() => void startEscrow()}
            >
              {checkout('confirmAndLock')}
            </Button>
          </Card>
        )}

        {dataState === 'live' && (payment || ledger) && (
          <div className="space-y-6">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-ink-soft">{escrow('amount')}</p>
                  <p className="num text-2xl font-bold text-forest">
                    {payment
                      ? formatPrice(payment.amount)
                      : held === null
                        ? statusLine('unavailable')
                        : formatPrice(held)}
                  </p>
                </div>
                {ledger ? (
                  <StatusDot
                    state={ledger.escrow_status === 'held' ? 'ok' : 'warn'}
                    label={`${ledger.payment_status} · ${ledger.escrow_status}`}
                  />
                ) : payment ? (
                  <StatusDot state="warn" label={`${payment.status} · ${payment.escrow_status}`} />
                ) : null}
              </div>
              <p className="num mt-3 font-mono text-xs text-ink-soft">
                {escrow('orderId')}: {order?.id ?? orderId ?? statusLine('unavailable')}
              </p>
              {payment || ledger ? (
                <p className="num mt-1 font-mono text-xs text-ink-soft">
                  {escrow('contractHash')}: {payment?.id ?? ledger?.payment_id ?? ''}
                </p>
              ) : null}
              {payment?.bank_instructions
                ? Object.entries(payment.bank_instructions).map(([key, value]) => (
                    <p key={key} className="mt-1 text-sm text-ink-soft">
                      {value}
                    </p>
                  ))
                : null}
            </Card>

            <Card density="compact">
              <h2 className="mb-3 font-medium text-ink">{escrow('eventTimeline')}</h2>
              {ledger && ledger.entries.length > 0 ? (
                <ul className="space-y-2">
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
              ) : (
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              )}
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {common('back')}
              </Button>
              {payment && payment.gateway === 'bank' ? (
                <Button
                  variant="primary"
                  onClick={() =>
                    router.push(
                      `/${locale}/market/checkout/transaction-key?order=${encodeURIComponent(payment.order_id)}&payment=${encodeURIComponent(payment.id)}`,
                    )
                  }
                >
                  {checkout('transactionKey')}
                </Button>
              ) : null}
              {payment?.redirect_url ? (
                <Button
                  variant="secondary"
                  onClick={() =>
                    router.push(
                      `/${locale}/market/checkout/confirmation?order=${encodeURIComponent(payment.order_id)}&payment=${encodeURIComponent(payment.id)}`,
                    )
                  }
                >
                  {checkout('confirmation')}
                </Button>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
