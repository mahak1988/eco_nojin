'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { use, useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, type ApiResult, classifyApiFailure } from '@/lib/api/cart';
import {
  ESCROW_SOURCE,
  type EscrowEntry,
  type EscrowStatusResponse,
  getEscrowStatus,
  heldAmount,
  openDispute,
  settleOrder,
} from '@/lib/api/escrow';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

const HOLD_STATES = new Set(['held', 'released', 'refunded']);
const CLOSED_STATES = new Set(['released', 'refunded', 'reversed', 'completed']);

function dotState(escrowStatus: string): 'ok' | 'warn' | 'down' {
  if (CLOSED_STATES.has(escrowStatus)) return escrowStatus === 'refunded' ? 'down' : 'ok';
  if (HOLD_STATES.has(escrowStatus)) return 'ok';
  return 'warn';
}

export default function EscrowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order') ?? '';

  const t = useTranslations('market.escrow');
  const common = useTranslations('common');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [escrow, setEscrow] = useState<EscrowStatusResponse | null>(null);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');
  const [actionError, setActionError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [acting, setActing] = useState(false);

  const source = `${ESCROW_SOURCE}/${encodeURIComponent(id)}/escrow`;

  const load = useCallback(async () => {
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const result = await getEscrowStatus(id);
    if (!result.ok) {
      const kind = classifyApiFailure(result.status);
      setFailureKind(kind);
      setDetail(result.error);
      setEscrow(null);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }
    setEscrow(result.data);
    setDataState('live');
  }, [id]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
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

  const amount = escrow ? heldAmount(escrow.entries) : null;
  const closed = escrow ? CLOSED_STATES.has(escrow.escrow_status) : false;

  const runTransition = async (action: () => Promise<ApiResult<unknown>>) => {
    setActing(true);
    setActionError('');
    try {
      const result = await action();
      if (!result.ok) {
        setFailureKind(classifyApiFailure(result.status));
        setActionError(result.error);
        return;
      }
      await load();
    } finally {
      setActing(false);
      setShowConfirm(false);
    }
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);

  const renderEntry = (entry: EscrowEntry) => (
    <li key={entry.id} className="relative border-s-2 border-forest pb-2 ps-4">
      <span
        aria-hidden="true"
        className="absolute start-[-5px] top-1 h-3 w-3 rounded-full bg-forest"
      />
      <p className="num font-mono text-xs text-ink-soft">{entry.entry_type}</p>
      {entry.amount !== null ? (
        <p className="num text-sm text-ink">{formatPrice(entry.amount)}</p>
      ) : null}
    </li>
  );

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={() => router.push(`/${locale}/market/cart`)}
              className="text-sm text-ink-soft underline hover:text-ink"
            >
              {common('back')}
            </button>
          </nav>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {t('title')}: <span className="num font-mono">{escrow?.payment_id ?? id}</span>
            </h1>
            <ProvenanceStamp
              source={source}
              label={t('escrowProvenance')}
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
            emptyMessage={t('dataUnavailable')}
          />
        )}

        {dataState === 'live' && escrow && (
          <div className="space-y-6">
            {actionError ? (
              <p role="alert" className="rounded-md bg-clay/10 p-3 text-sm text-clay">
                {actionError}
              </p>
            ) : null}

            <Card density="compact">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-ink-soft">{t('amount')}</p>
                  <p className="num text-2xl font-bold text-forest">
                    {amount === null ? statusLine('unavailable') : formatPrice(amount)}
                  </p>
                </div>
                <StatusDot
                  state={dotState(escrow.escrow_status)}
                  label={`${escrow.payment_status} · ${escrow.escrow_status}`}
                />
              </div>
              <div className="mt-4 space-y-1">
                <p className="text-xs text-ink-soft">
                  {t('orderId')}:{' '}
                  <span className="num font-mono">{orderId || statusLine('unavailable')}</span>
                </p>
                <p className="text-xs text-ink-soft">
                  {t('contractHash')}:{' '}
                  <span className="num font-mono">
                    {escrow.entries[0]?.id ?? statusLine('unavailable')}
                  </span>
                </p>
              </div>
            </Card>

            <Card density="compact">
              <h2 className="mb-3 font-medium text-ink">{t('eventTimeline')}</h2>
              {escrow.entries.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              ) : (
                <ul className="space-y-4">{escrow.entries.map(renderEntry)}</ul>
              )}
            </Card>

            <Card density="compact">
              <h2 className="mb-3 font-medium text-ink">{t('parties')}</h2>
              <p role="status" className="text-sm text-ink-soft">
                {statusLine('unavailable')}
              </p>
            </Card>

            {closed ? (
              <Card density="compact">
                <p className="text-sm text-ink-soft">{t('escrowComplete')}</p>
              </Card>
            ) : orderId ? (
              <div className="flex flex-wrap gap-3">
                <Button variant="primary" loading={acting} onClick={() => setShowConfirm(true)}>
                  {t('releaseFunds')}
                </Button>
                <Button
                  variant="danger"
                  loading={acting}
                  onClick={() => void runTransition(() => openDispute(orderId))}
                >
                  {t('openDispute')}
                </Button>
              </div>
            ) : (
              <Card density="compact">
                <p role="status" className="text-sm text-ink-soft">
                  {statusLine('unavailable')}
                </p>
              </Card>
            )}

            {showConfirm && (
              <Card density="cozy">
                <h3 className="mb-2 font-medium text-ink">{t('confirmRelease')}</h3>
                <p className="mb-4 text-sm text-ink-soft">{t('confirmReleaseDesc')}</p>
                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    size="sm"
                    loading={acting}
                    onClick={() => void runTransition(() => settleOrder(orderId))}
                  >
                    {t('confirmReleaseButton')}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setShowConfirm(false)}>
                    {common('cancel')}
                  </Button>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
