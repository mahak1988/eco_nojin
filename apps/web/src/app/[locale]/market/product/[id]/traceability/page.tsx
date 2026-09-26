'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { use, useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import { getProductTrace, type ProductTrace, productTraceSource } from '@/lib/api/market';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

export default function ProductTraceabilityPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: routeLocale, id } = use(params);
  const locale = routeLocale || 'fa';

  const product = useTranslations('market.product');
  const market = useTranslations('market');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const router = useRouter();

  const [trace, setTrace] = useState<ProductTrace | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const source = productTraceSource(id);

  const load = useCallback(async () => {
    if (!id) return;
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await getProductTrace(id);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setTrace(null);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setTrace(result.data);
    setDataState(result.data.events.length > 0 ? 'live' : 'empty');
  }, [id]);

  useEffect(() => {
    setDataState('loading');
    void load();
  }, [load]);

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
              onClick={() => router.push(`/${locale}/market/product/${id}`)}
              className="text-ink-soft underline hover:text-ink"
            >
              {product('backToMarket')}
            </button>
            <span aria-hidden="true" className="text-ink-soft">
              /
            </span>
            <span className="num font-mono text-xs text-ink-soft">{id}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {product('traceabilityTitle')}
            </h1>
            <ProvenanceStamp
              source={source}
              label={product('productProvenance')}
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
            emptyMessage={market('empty')}
            emptyAction={
              <Button
                variant="primary"
                onClick={() => router.push(`/${locale}/market/product/${id}`)}
              >
                {product('backToMarket')}
              </Button>
            }
          />
        )}

        {dataState === 'live' && trace && (
          <div className="space-y-6">
            <Card density="compact">
              <dl className="space-y-2">
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{product('traceability')}</dt>
                  <dd className="num break-all font-mono text-end text-xs text-forest">
                    {trace.traceability_code ?? statusLine('unavailable')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-ink-soft">{common('evidence')}</dt>
                  <dd className="num break-all text-end font-mono text-xs text-ink-soft">
                    {trace.qr_data ?? statusLine('unavailable')}
                  </dd>
                </div>
              </dl>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{product('traceabilityTitle')}</h2>
              <ol className="space-y-5">
                {trace.events.map((entry) => (
                  <li
                    key={`${entry.timestamp}-${entry.event}`}
                    className="relative border-s-2 border-forest ps-4"
                  >
                    <span
                      aria-hidden="true"
                      className="absolute start-[-5px] top-1 h-3 w-3 rounded-full bg-forest"
                    />
                    <p className="text-sm font-medium text-ink">{entry.event}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <StatusDot state="ok" label={entry.location || statusLine('unavailable')} />
                      <time className="num text-xs text-ink-soft" dateTime={entry.timestamp}>
                        {formatDateTime(entry.timestamp)}
                      </time>
                    </div>
                    {entry.actor ? (
                      <p className="mt-1 text-xs text-ink-soft">{entry.actor}</p>
                    ) : null}
                    {entry.notes ? (
                      <p className="mt-1 text-sm text-ink-soft">{entry.notes}</p>
                    ) : null}
                  </li>
                ))}
              </ol>
            </Card>

            <Button variant="ghost" onClick={() => router.push(`/${locale}/market/product/${id}`)}>
              {common('back')}
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}
