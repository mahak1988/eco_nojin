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

const CLOSED_STATUSES: ReadonlySet<string> = new Set(['delivered', 'cancelled']);

function orderDot(status: string): 'ok' | 'warn' | 'down' {
  if (status === 'cancelled') return 'down';
  if (status === 'delivered') return 'ok';
  return 'warn';
}

function timelineSource(orderId: string): string {
  return `${ORDERS_SOURCE}/${encodeURIComponent(orderId)}/track`;
}

export default function OrderTimelinePage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: routeLocale, id } = use(params);
  const locale = routeLocale || 'fa';

  const escrow = useTranslations('market.escrow');
  const checkout = useTranslations('market.checkout');
  const template = useTranslations('market.template');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [timeline, setTimeline] = useState<OrderTimelineResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const source = timelineSource(id);

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
      setTimeline(null);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setTimeline(result.data);
    setDataState(result.data.timeline.length > 0 ? 'live' : 'empty');
  }, [id]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setTimeline(null);
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
              {escrow('eventTimeline')}
            </h1>
            <ProvenanceStamp
              source={source}
              label={template('source')}
              method={dataState === 'live' ? statusLine('realData') : undefined}
            />
          </div>
          {timeline ? (
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <StatusDot
                state={orderDot(timeline.current_status)}
                label={timeline.current_status}
              />
              <span className="num font-mono text-xs text-ink-soft">
                {escrow('orderId')}: {timeline.order_number}
              </span>
            </div>
          ) : null}
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

        {dataState === 'live' && timeline && (
          <>
            <Card density="compact">
              {timeline.timeline.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              ) : (
                <ol className="space-y-5">
                  {timeline.timeline.map((entry) => (
                    <li
                      key={`${entry.timestamp}-${entry.status}`}
                      className="relative border-s-2 border-forest ps-4"
                    >
                      <span
                        aria-hidden="true"
                        className="absolute start-[-5px] top-1 h-3 w-3 rounded-full bg-forest"
                      />
                      <p className="text-sm font-medium text-ink">{entry.title}</p>
                      <p className="mt-1 text-sm text-ink-soft">{entry.description}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <StatusDot state={orderDot(entry.status)} label={entry.status} />
                        <time className="num text-xs text-ink-soft" dateTime={entry.timestamp}>
                          {formatDateTime(entry.timestamp)}
                        </time>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </Card>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button variant="ghost" onClick={() => router.push(`/${locale}/market/orders`)}>
                {common('back')}
              </Button>
              {CLOSED_STATUSES.has(timeline.current_status) ? null : (
                <Button
                  variant="secondary"
                  onClick={() => router.push(`/${locale}/market/orders/${id}/dispute`)}
                >
                  {escrow('openDispute')}
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
