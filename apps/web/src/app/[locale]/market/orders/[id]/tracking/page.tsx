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
import {
  type ApiFailureKind,
  classifyApiFailure,
  getOrderTimeline,
  ORDERS_SOURCE,
  type OrderTimelineResponse,
} from '@/lib/api/cart';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

/**
 * Lifecycle the gateway reports for an order
 * (`services/marketplace/models:OrderStatus`). A stage is only marked as passed
 * when the server status is at or beyond it, so no step is ever assumed.
 */
const STAGES = ['pending', 'confirmed', 'shipped', 'delivered'] as const;

function stageState(stage: string, current: string): 'ok' | 'warn' | 'down' {
  if (current === 'cancelled') return 'down';
  if (current === stage) return 'warn';
  return STAGES.indexOf(stage as (typeof STAGES)[number]) <
    STAGES.indexOf(current as (typeof STAGES)[number])
    ? 'ok'
    : 'warn';
}

function trackingSource(orderId: string): string {
  return `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/track`;
}

export default function OrderTrackingPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: routeLocale, id } = use(params);
  const locale = routeLocale || 'fa';

  const escrow = useTranslations('market.escrow');
  const checkout = useTranslations('market.checkout');
  const template = useTranslations('market.template');
  const product = useTranslations('market.product');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [tracking, setTracking] = useState<OrderTimelineResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const source = trackingSource(id);

  const load = useCallback(async () => {
    if (!id) return;
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await getOrderTimeline(id);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setTracking(null);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setTracking(result.data);
    setDataState(result.data.timeline.length > 0 ? 'live' : 'empty');
  }, [id]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setTracking(null);
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
              {escrow('orderId')}:{' '}
              <span className="num font-mono">{tracking?.order_number ?? id}</span>
            </h1>
            <ProvenanceStamp
              source={source}
              label={template('source')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
        </header>

        {dataState !== 'live' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={escrow('dataUnavailable')}
          />
        )}

        {dataState === 'live' && tracking && (
          <div className="space-y-6">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-ink-soft">{product('status')}</p>
                <StatusDot
                  state={
                    tracking.current_status === 'cancelled'
                      ? 'down'
                      : tracking.current_status === 'delivered'
                        ? 'ok'
                        : 'warn'
                  }
                  label={tracking.current_status}
                />
              </div>
              <div className="mt-4 flex justify-between gap-4 border-t border-line pt-3">
                <span className="text-sm text-ink-soft">{product('shipping')}</span>
                <span className="text-sm text-ink">{statusLine('unavailable')}</span>
              </div>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{escrow('eventTimeline')}</h2>
              <ol className="space-y-3">
                {STAGES.map((stage) => (
                  <li key={stage} className="flex items-center justify-between gap-3">
                    <StatusDot state={stageState(stage, tracking.current_status)} label={stage} />
                  </li>
                ))}
              </ol>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{common('evidence')}</h2>
              {tracking.timeline.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              ) : (
                <ul className="space-y-3">
                  {tracking.timeline.map((entry) => (
                    <li
                      key={`${entry.timestamp}-${entry.status}`}
                      className="border-b border-line/50 pb-3 last:border-0"
                    >
                      <p className="text-sm text-ink">{entry.description}</p>
                      <time className="num block text-xs text-ink-soft" dateTime={entry.timestamp}>
                        {formatDateTime(entry.timestamp)}
                      </time>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/orders`)}>
                {common('back')}
              </Button>
              <Button
                variant="secondary"
                onClick={() => router.push(`/${locale}/market/orders/${id}/timeline`)}
              >
                {escrow('eventTimeline')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
