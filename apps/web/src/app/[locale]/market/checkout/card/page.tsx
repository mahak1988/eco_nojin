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
import { createPayment, ESCROW_SOURCE, type PaymentResponse } from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

/**
 * The card step is a redirect only. `POST /payments` answers with the
 * gateway's `redirect_url` and the gateway page is what receives card data
 * (`payments_service.py::PaymentGateways.create`), so this route never renders a
 * card number, expiry or CVV field and never posts one.
 */
const CARD_GATEWAY = 'zarinpal' as const;

export default function CardPaymentPage() {
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

  const [order, setOrder] = useState<OrderListEntry | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [acting, setActing] = useState(false);

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    if (!orderId) {
      setOrder(null);
      setDataState('unavailable');
      return;
    }
    const result = await getOrder(orderId);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
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
    setOrder(result.data);
    setDataState('live');
  }, [orderId]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setOrder(null);
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
   * Creates the gateway payment for the server-computed order total and hands
   * the browser to the gateway URL it returned.
   */
  const startGatewayPayment = useCallback(async () => {
    if (!user || !order) return;
    setActing(true);
    setDetail('');
    try {
      const result = await createPayment({
        orderId: order.id,
        amount: order.total_price,
        paymentMethod: CARD_GATEWAY,
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
      if (result.data.redirect_url) {
        window.location.assign(result.data.redirect_url);
      }
    } finally {
      setActing(false);
    }
  }, [user, order]);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/checkout/escrow-setup`)}
              className="text-ink-soft underline hover:text-ink"
            >
              {checkout('escrowSetup')}
            </button>
            <span aria-hidden="true" className="text-ink-soft">
              /
            </span>
            <span className="text-ink-soft">{checkout('card')}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{checkout('card')}</h1>
            <ProvenanceStamp
              source={ESCROW_SOURCE}
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
            onRetry={orderId ? () => void load() : undefined}
          />
        )}

        {detail && dataState === 'live' ? (
          <p role="alert" className="mb-6 rounded-md bg-clay/10 p-3 text-sm text-clay">
            {detail}
          </p>
        ) : null}

        {dataState === 'live' && order && (
          <div className="space-y-6">
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
                <div className="flex justify-between gap-4 border-t border-line pt-2">
                  <dt className="font-medium text-ink">{escrow('amount')}</dt>
                  <dd className="num text-lg font-bold text-forest">
                    {formatPrice(order.total_price)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{checkout('card')}</dt>
                  <dd className="text-end text-sm text-ink">{statusLine('unavailable')}</dd>
                </div>
              </dl>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <Button
                  variant="primary"
                  loading={acting}
                  onClick={() => void startGatewayPayment()}
                >
                  {common('open')}
                </Button>
                {payment?.redirect_url ? (
                  <a
                    href={payment.redirect_url}
                    rel="noopener noreferrer"
                    className="text-sm text-water underline"
                  >
                    {common('open')}
                  </a>
                ) : null}
              </div>
            </Card>

            {payment ? (
              <Card density="compact">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="num font-mono text-sm text-forest">{payment.id}</p>
                  <StatusDot state="warn" label={`${payment.status} · ${payment.escrow_status}`} />
                </div>
                {payment.redirect_url ? null : (
                  <p className="mt-2 text-sm text-ink-soft">{statusLine('unavailable')}</p>
                )}
              </Card>
            ) : null}

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {common('back')}
              </Button>
              {payment ? (
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
