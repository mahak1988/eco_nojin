'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { use, useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure, ORDERS_SOURCE } from '@/lib/api/cart';
import { type EscrowTransitionResponse, openDispute } from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

function disputeSource(orderId: string): string {
  return `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/dispute`;
}

function disputeDot(state: string): 'ok' | 'warn' | 'down' {
  if (state === 'disputed' || state === 'dispute_window_open') return 'warn';
  if (state === 'released' || state === 'completed') return 'ok';
  return 'down';
}

export default function OrderDisputePage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: routeLocale, id } = use(params);
  const locale = routeLocale || 'fa';

  const escrow = useTranslations('market.escrow');
  const checkout = useTranslations('market.checkout');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [record, setRecord] = useState<EscrowTransitionResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('unavailable');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [acting, setActing] = useState(false);

  const source = disputeSource(id);

  /**
   * `POST /orders/{id}/dispute` is the only dispute contract the gateway
   * exposes, and it is a transition rather than a read: there is nothing to show
   * before the buyer opens the window, so the page starts unavailable instead of
   * pretending a dispute record already exists.
   */
  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setRecord(null);
      setDataState('unauthenticated');
      return;
    }
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setRecord(null);
    setDataState('unavailable');
  }, [authLoading, user]);

  useEffect(() => {
    if (dataState !== 'offline') return;
    return registerConnectivityListeners((online) => {
      if (!online) return;
      if (!user) {
        setDataState('unauthenticated');
        return;
      }
      setDataState('unavailable');
    });
  }, [dataState, user]);

  const open = useCallback(async () => {
    if (!id || !user) return;
    setActing(true);
    setDetail('');
    try {
      const result = await openDispute(id);
      if (!result.ok) {
        const kind = classifyApiFailure(result.status);
        setFailureKind(kind);
        setDetail(result.error);
        setRecord(null);
        setDataState(
          kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error',
        );
        return;
      }
      setRecord(result.data);
      setDataState('live');
    } finally {
      setActing(false);
    }
  }, [id, user]);

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
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/orders`)}
              className="text-ink-soft underline hover:text-ink"
            >
              {checkout('viewOrders')}
            </button>
            <span aria-hidden="true" className="text-ink-soft">
              /
            </span>
            <span className="num font-mono text-xs text-ink-soft">{id}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {escrow('openDispute')}
            </h1>
            <ProvenanceStamp
              source={source}
              label={escrow('escrowProvenance')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        {dataState !== 'live' && dataState !== 'unavailable' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={dataState === 'offline' ? () => void open() : undefined}
          />
        )}

        {dataState === 'unavailable' && (
          <Card density="cozy">
            <p role="status" className="text-sm text-ink-soft">
              {statusLine('unavailable')}
            </p>
            <Button variant="danger" className="mt-4" loading={acting} onClick={() => void open()}>
              {escrow('openDispute')}
            </Button>
          </Card>
        )}

        {dataState === 'live' && record && (
          <div className="space-y-6">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-ink-soft">{escrow('orderId')}</p>
                  <p className="num font-mono text-sm text-ink">{record.order_id}</p>
                </div>
                <StatusDot state={disputeDot(record.state)} label={record.state} />
              </div>
              <dl className="mt-4 space-y-2">
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{escrow('contractHash')}</dt>
                  <dd className="num break-all font-mono text-end text-sm text-ink">
                    {record.escrow_id}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{common('pending')}</dt>
                  <dd className="text-sm text-ink">{record.status ?? statusLine('unavailable')}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{common('evidence')}</dt>
                  <dd className="text-sm text-ink">
                    {record.dispute_deadline ? (
                      <time dateTime={record.dispute_deadline}>
                        {formatDateTime(record.dispute_deadline)}
                      </time>
                    ) : (
                      statusLine('unavailable')
                    )}
                  </dd>
                </div>
                {record.remaining_seconds !== undefined && record.remaining_seconds !== null ? (
                  <div className="flex justify-between gap-4">
                    <dt className="text-sm text-ink-soft">{escrow('escrowStatus')}</dt>
                    <dd className="num text-sm text-ink">
                      {Math.max(0, Math.round(record.remaining_seconds))}
                    </dd>
                  </div>
                ) : null}
              </dl>
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/orders`)}>
                {common('back')}
              </Button>
              <Button
                variant="secondary"
                onClick={() => router.push(`/${locale}/market/orders/${id}/tracking`)}
              >
                {checkout('viewOrders')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
