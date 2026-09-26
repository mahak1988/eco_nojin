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
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import {
  confirmPayment,
  ESCROW_SOURCE,
  type EscrowStatusResponse,
  getEscrowStatus,
  heldAmount,
  isValidTransactionKey,
} from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function TransactionKeyPage() {
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

  const [ledger, setLedger] = useState<EscrowStatusResponse | null>(null);
  const [reference, setReference] = useState('');
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
    if (!paymentId) {
      setLedger(null);
      setDataState('unavailable');
      return;
    }
    const result = await getEscrowStatus(paymentId);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
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
    setLedger(result.data);
    setDataState('live');
  }, [paymentId]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
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
   * A bank payment can only enter escrow hold once the gateway verifies the
   * transfer, which requires the transfer reference the bank issued. The field
   * is gated by the same 120-character contract the gateway validates.
   */
  const verifyTransfer = useCallback(async () => {
    if (!paymentId || !isValidTransactionKey(reference)) return;
    setActing(true);
    setDetail('');
    try {
      const result = await confirmPayment(paymentId, reference);
      if (!result.ok) {
        const kind = classifyApiFailure(result.status);
        setFailureKind(kind);
        setDetail(result.error);
        return;
      }
      await load();
    } finally {
      setActing(false);
    }
  }, [paymentId, reference, load]);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const held = ledger ? heldAmount(ledger.entries) : null;
  const verified = ledger?.escrow_status === 'held';

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
            <span className="text-ink-soft">{checkout('transactionKey')}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {checkout('transactionKey')}
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
            onRetry={paymentId ? () => void load() : undefined}
          />
        )}

        {dataState === 'live' && ledger && (
          <div className="space-y-6">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-ink-soft">{escrow('amount')}</p>
                  <p className="num text-2xl font-bold text-forest">
                    {held === null ? statusLine('unavailable') : formatPrice(held)}
                  </p>
                </div>
                <StatusDot
                  state={verified ? 'ok' : 'warn'}
                  label={`${ledger.payment_status} · ${ledger.escrow_status}`}
                />
              </div>
              <p className="num mt-3 font-mono text-xs text-ink-soft">
                {escrow('orderId')}: {orderId || statusLine('unavailable')}
              </p>
            </Card>

            {verified ? (
              <Card density="cozy">
                <p className="text-sm text-ink-soft">{escrow('escrowComplete')}</p>
              </Card>
            ) : (
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  void verifyTransfer();
                }}
              >
                <div>
                  <label htmlFor="transaction-key" className="mb-1 block text-sm text-ink-soft">
                    {checkout('transactionKey')}
                  </label>
                  <input
                    id="transaction-key"
                    type="text"
                    autoComplete="off"
                    maxLength={120}
                    value={reference}
                    onChange={(event) => setReference(event.target.value)}
                    className="w-full rounded border border-line bg-surface px-4 py-2 text-ink"
                  />
                </div>
                {detail ? (
                  <p role="alert" className="rounded-md bg-clay/10 p-3 text-sm text-clay">
                    {detail}
                  </p>
                ) : null}
                <Button
                  variant="primary"
                  type="submit"
                  loading={acting}
                  disabled={!isValidTransactionKey(reference)}
                >
                  {checkout('confirmAndLock')}
                </Button>
              </form>
            )}

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/checkout`)}>
                {common('back')}
              </Button>
              <Button
                variant="secondary"
                onClick={() =>
                  router.push(
                    `/${locale}/market/checkout/confirmation?order=${encodeURIComponent(orderId)}&payment=${encodeURIComponent(paymentId)}`,
                  )
                }
              >
                {checkout('confirmation')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
