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
  type CartLine,
  type CreateOrderResponse,
  classifyApiFailure,
  createOrder,
  getCart,
  ORDERS_SOURCE,
  removeFromCart,
} from '@/lib/api/cart';
import {
  confirmPayment,
  createPayment,
  type EscrowStatusResponse,
  getEscrowStatus,
  PAYMENT_GATEWAYS,
  type PaymentGateway,
  type PaymentResponse,
} from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

type CheckoutStep = 'cart' | 'payment' | 'confirmation';

interface CartItem {
  id: string;
  product: string;
  quantity: number;
  unitPrice: number;
}

function toCartItem(line: CartLine): CartItem {
  return {
    id: line.product_id,
    product: line.product_name ?? line.product_id,
    quantity: line.quantity,
    unitPrice: line.price ?? 0,
  };
}

export default function CheckoutPage() {
  const t = useTranslations('market.checkout');
  const common = useTranslations('common');
  const nav = useTranslations('nav');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [step, setStep] = useState<CheckoutStep>('cart');
  const [items, setItems] = useState<CartItem[]>([]);
  const [subtotal, setSubtotal] = useState(0);
  const [cartState, setCartState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const [contractAccepted, setContractAccepted] = useState(false);
  const [gateway, setGateway] = useState<PaymentGateway | null>(null);
  const [transactionKey, setTransactionKey] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [orders, setOrders] = useState<CreateOrderResponse[]>([]);
  const [payments, setPayments] = useState<PaymentResponse[]>([]);
  const [escrow, setEscrow] = useState<Record<string, EscrowStatusResponse>>({});

  const load = useCallback(async () => {
    if (!isOnline()) {
      setCartState('offline');
      return;
    }
    setDetail('');
    const result = await getCart();
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setCartState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    const next = result.data.items.map(toCartItem);
    setItems(next);
    setSubtotal(result.data.subtotal);
    setCartState(next.length > 0 ? 'live' : 'empty');
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setCartState('unauthenticated');
      setItems([]);
      return;
    }
    setCartState('loading');
    void load();
  }, [authLoading, user, load]);

  // Refetch the real cart as soon as connectivity returns.
  useEffect(() => {
    if (!user) return;
    return registerConnectivityListeners((online) => {
      if (online && cartState === 'offline') void load();
    });
  }, [user, cartState, load]);

  const loadEscrow = useCallback(async (paymentId: string) => {
    const result = await getEscrowStatus(paymentId);
    if (result.ok) {
      setEscrow((current) => ({ ...current, [paymentId]: result.data }));
    }
  }, []);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const buyerName = user?.full_name ?? user?.email ?? '';

  type Placement =
    | { ok: true; orders: CreateOrderResponse[]; payments: PaymentResponse[] }
    | {
        ok: false;
        error: string;
        status: number;
        orders: CreateOrderResponse[];
        payments: PaymentResponse[];
      };

  /**
   * Orders are created one by one so a rejected line cannot leave a silently
   * half-placed order, and every payment is charged the server-computed
   * `total_price` — never a client-side estimate. Whatever was really created
   * comes back with the outcome so a partial failure still reads as a failure.
   */
  const placeOrdersAndPayments = async (): Promise<Placement> => {
    if (!user || items.length === 0 || !gateway) {
      return { ok: false, error: t('apiUnavailable'), status: 0, orders: [], payments: [] };
    }
    const created: CreateOrderResponse[] = [];
    for (const item of items) {
      const result = await createOrder({
        productId: item.id,
        buyerName,
        quantityKg: item.quantity,
      });
      if (!result.ok) {
        return { ...result, orders: created, payments: [] };
      }
      created.push(result.data);
    }

    const charged: PaymentResponse[] = [];
    for (const order of created) {
      if (!(order.total_price > 0)) {
        return {
          ok: false,
          error: t('apiUnavailable'),
          status: 0,
          orders: created,
          payments: charged,
        };
      }
      const result = await createPayment({
        orderId: order.order_id,
        amount: order.total_price,
        paymentMethod: gateway,
        description: order.product_name,
      });
      if (!result.ok) {
        return { ...result, orders: created, payments: charged };
      }
      charged.push(result.data);
    }
    return { ok: true, orders: created, payments: charged };
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setDetail('');
    try {
      const result = await placeOrdersAndPayments();
      setOrders(result.orders);
      setPayments(result.payments);
      if (!result.ok) {
        setFailureKind(classifyApiFailure(result.status));
        setDetail(result.error);
        // A failure after order creation must not look like a success.
        if (result.orders.length > 0 || result.payments.length > 0) {
          setStep('confirmation');
        }
        return;
      }
      const cleared = await Promise.all(items.map((item) => removeFromCart(item.id)));
      if (cleared.some((result) => !result.ok)) {
        setDetail(t('apiUnavailable'));
      }
      setStep('confirmation');
      await Promise.all(result.payments.map((payment) => loadEscrow(payment.id)));
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmBankPayment = async (payment: PaymentResponse) => {
    setSubmitting(true);
    setDetail('');
    try {
      const result = await confirmPayment(payment.id, transactionKey);
      if (!result.ok) {
        setFailureKind(classifyApiFailure(result.status));
        setDetail(result.error);
        return;
      }
      setPayments((current) =>
        current.map((item) => (item.id === payment.id ? result.data.payment : item)),
      );
      await loadEscrow(payment.id);
    } finally {
      setSubmitting(false);
    }
  };

  const steps: Array<{ key: CheckoutStep; label: string }> = [
    { key: 'cart', label: t('step1Cart') },
    { key: 'payment', label: t('step2Escrow') },
    { key: 'confirmation', label: t('step3Confirm') },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-6 flex flex-wrap items-center gap-3">
          <h1 className="display flex-1 text-3xl font-bold text-ink sm:text-4xl">
            {t('cartReview')}
          </h1>
          <ProvenanceStamp
            source={ORDERS_SOURCE}
            label={t('checkoutProvenance')}
            method={cartState === 'live' ? statusLine('realData') : undefined}
          />
        </header>

        <ol className="mb-8 flex flex-wrap items-center gap-2">
          {steps.map((entry, index) => {
            const activeIndex = steps.findIndex((item) => item.key === step);
            const state = entry.key === step ? 'ok' : index < activeIndex ? 'ok' : 'warn';
            return (
              <li key={entry.key} className="flex items-center gap-2">
                <StatusDot state={state} label={entry.label} />
                {index < steps.length - 1 ? (
                  <span aria-hidden="true" className="h-px w-6 bg-line" />
                ) : null}
              </li>
            );
          })}
        </ol>

        {step !== 'confirmation' && cartState !== 'live' && (
          <MarketDataStateNotice
            state={cartState}
            locale={locale}
            detail={cartState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={t('cartReview')}
            emptyAction={
              <Button variant="primary" onClick={() => router.push(`/${locale}/market/cart`)}>
                {nav('market')}
              </Button>
            }
          />
        )}

        {step === 'cart' && cartState === 'live' && (
          <Card density="compact">
            <h2 className="mb-4 font-medium text-ink">{t('cartReview')}</h2>
            <div className="mb-6 space-y-3">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between gap-4">
                  <span className="text-ink-soft">
                    {item.product} × {item.quantity}
                  </span>
                  <span className="num text-ink">
                    {formatPrice(item.unitPrice * item.quantity)}
                  </span>
                </div>
              ))}
            </div>
            <div className="space-y-2 border-t border-line pt-4">
              <div className="flex justify-between">
                <span className="text-ink-soft">{t('subtotal')}</span>
                <span className="num text-ink">{formatPrice(subtotal)}</span>
              </div>
              <div className="flex justify-between border-t border-line pt-2">
                <span className="font-bold text-ink">{common('total')}</span>
                <span className="num text-xl font-bold text-forest">{formatPrice(subtotal)}</span>
              </div>
            </div>
            <Button
              variant="primary"
              className="mt-6 w-full"
              onClick={() => {
                setDetail('');
                setStep('payment');
              }}
            >
              {common('proceedToCheckout')}
            </Button>
          </Card>
        )}

        {step === 'payment' && (
          <Card density="compact">
            <h2 className="mb-4 font-medium text-ink">{t('escrowSetup')}</h2>
            {detail ? (
              <p role="alert" className="mb-4 rounded-md bg-clay/10 p-3 text-sm text-clay">
                {detail}
              </p>
            ) : null}

            <fieldset className="mb-6">
              <legend className="mb-2 text-sm text-ink-soft">{t('escrowSetup')}</legend>
              <div className="space-y-2">
                {PAYMENT_GATEWAYS.map((option) => (
                  <label key={option} className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="gateway"
                      checked={gateway === option}
                      onChange={() => setGateway(option)}
                      className="h-4 w-4"
                    />
                    <code className="font-mono text-sm text-ink">{option}</code>
                  </label>
                ))}
              </div>
            </fieldset>

            {gateway === 'bank' && (
              <div className="mb-6">
                <label htmlFor="transaction-key" className="mb-1 block text-sm text-ink-soft">
                  {t('transactionKey')}
                </label>
                <input
                  id="transaction-key"
                  type="text"
                  value={transactionKey}
                  onChange={(event) => setTransactionKey(event.target.value)}
                  className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
                />
              </div>
            )}

            <label className="mb-6 flex items-start gap-3">
              <input
                type="checkbox"
                checked={contractAccepted}
                onChange={(event) => setContractAccepted(event.target.checked)}
                className="mt-1 h-4 w-4"
              />
              <span className="text-sm text-ink-soft">{t('contractAcceptance')}</span>
            </label>

            <Button
              variant="primary"
              className="w-full"
              loading={submitting}
              disabled={!contractAccepted || !gateway}
              onClick={() => void handleSubmit()}
            >
              {contractAccepted && gateway ? t('confirmAndLock') : t('acceptContractFirst')}
            </Button>
          </Card>
        )}

        {step === 'confirmation' && (
          <div className="space-y-6">
            {detail ? (
              <p role="alert" className="rounded-md bg-clay/10 p-3 text-sm text-clay">
                {detail}
              </p>
            ) : null}

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{t('orderPlaced')}</h2>
              {orders.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {t('apiUnavailable')}
                </p>
              ) : null}
              <div className="space-y-3">
                {orders.map((order) => (
                  <div key={order.order_id} className="border-b border-line/50 pb-3">
                    <p className="font-medium text-ink">{order.product_name}</p>
                    <p className="num text-sm text-ink-soft">
                      {formatPrice(order.total_price)} · {order.status}
                    </p>
                    {order.traceability_code ? (
                      <p className="num mt-1 font-mono text-xs text-forest">
                        {order.traceability_code}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{t('transactionKey')}</h2>
              {payments.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {t('apiUnavailable')}
                </p>
              ) : null}
              <div className="space-y-4">
                {payments.map((payment) => {
                  const ledger = escrow[payment.id];
                  const instructions = payment.bank_instructions;
                  return (
                    <div key={payment.id} className="border-b border-line/50 pb-4 last:border-0">
                      <p className="num font-mono text-sm text-forest">{payment.id}</p>
                      <p className="mt-1 text-sm text-ink-soft">
                        {payment.gateway} · {formatPrice(payment.amount)} · {payment.status}
                      </p>
                      {payment.redirect_url ? (
                        <a
                          href={payment.redirect_url}
                          className="mt-2 inline-block text-sm text-water underline"
                          rel="noopener noreferrer"
                        >
                          {common('open')}
                        </a>
                      ) : null}
                      {instructions
                        ? Object.entries(instructions).map(([key, value]) => (
                            <p key={key} className="mt-1 text-sm text-ink-soft">
                              {value}
                            </p>
                          ))
                        : null}

                      <h3 className="mt-4 mb-2 text-sm font-medium text-ink">
                        {t('escrowStatus')}
                      </h3>
                      {!ledger ? (
                        <p role="status" className="text-sm text-ink-soft">
                          {statusLine('unavailable')}
                        </p>
                      ) : (
                        <>
                          <StatusDot
                            state={ledger.escrow_status === 'held' ? 'ok' : 'warn'}
                            label={`${ledger.payment_status} · ${ledger.escrow_status}`}
                          />
                          <ul className="mt-2 space-y-1">
                            {ledger.entries.map((entry) => (
                              <li key={entry.id} className="num text-xs text-ink-soft">
                                {entry.entry_type}
                                {entry.amount !== null ? ` · ${formatPrice(entry.amount)}` : ''}
                              </li>
                            ))}
                          </ul>
                        </>
                      )}

                      {payment.gateway === 'bank' && payment.escrow_status !== 'held' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          className="mt-3"
                          loading={submitting}
                          disabled={!transactionKey}
                          onClick={() => void handleConfirmBankPayment(payment)}
                        >
                          {t('transactionKey')}
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>

            <div className="flex flex-wrap gap-4">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/cart`)}>
                {common('back')}
              </Button>
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => {
                  const paymentId = payments[0]?.id ?? '';
                  const orderId = orders[0]?.order_id ?? '';
                  router.push(`/${locale}/market/escrow/${paymentId}?order=${orderId}`);
                }}
                disabled={payments.length === 0}
              >
                {t('viewOrders')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
