'use client';

import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { type MarketDataState, MarketDataStateNotice } from '@/components/market/MarketDataState';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { Card } from '@/components/ui/Card';
import { type ApiFailureKind, classifyApiFailure } from '@/lib/api/cart';
import { apiGet } from '@/lib/api/client';
import { isOnline, registerConnectivityListeners } from '@/lib/offline/connectivity';

const WALLET_BASE = '/api/v1/ecowallet';

type WalletStateResponse = {
  user_id: string;
  balance: number | string;
  total_earned: number | string;
  total_redeemed: number | string;
  is_active: boolean;
};

type EarningsEntry = {
  date: string;
  earnings_type: string;
  amount: string;
  source: string;
  status: string;
  processed_at: string | null;
};

function walletSource(userId: string): string {
  return `${WALLET_BASE}/wallet/${encodeURIComponent(userId)}`;
}

/** The earnings feed carries no row id, so the returned fields form the key. */
function earningRowKey(entry: EarningsEntry): string {
  return [entry.date, entry.earnings_type, entry.source, entry.processed_at ?? ''].join('|');
}

export default function WalletPage() {
  const t = useTranslations('market.wallet');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [wallet, setWallet] = useState<WalletStateResponse | null>(null);
  const [earnings, setEarnings] = useState<EarningsEntry[]>([]);
  const [dataState, setDataState] = useState<MarketDataState>('loading');
  const [failureKind, setFailureKind] = useState<ApiFailureKind>('server');
  const [detail, setDetail] = useState('');

  const source = user ? walletSource(user.id) : WALLET_BASE;

  const load = useCallback(async () => {
    if (!user) return;
    if (!isOnline()) {
      setDataState('offline');
      return;
    }
    setDetail('');
    const [walletResult, earningsResult] = await Promise.all([
      apiGet<WalletStateResponse>(walletSource(user.id)),
      apiGet<EarningsEntry[]>(`${WALLET_BASE}/earnings?user_id=${encodeURIComponent(user.id)}`),
    ]);

    if (!walletResult.ok) {
      const kind = classifyApiFailure(walletResult.status);
      setFailureKind(kind);
      setDetail(walletResult.error);
      setWallet(null);
      setEarnings([]);
      setDataState(kind === 'offline' ? 'offline' : kind === 'auth' ? 'unauthenticated' : 'error');
      return;
    }

    setWallet(walletResult.data);
    // The earnings feed is a separate, optional capability: a failure there must
    // not blank out the balance the wallet endpoint already confirmed.
    setEarnings(earningsResult.ok ? earningsResult.data : []);
    setDataState('live');
  }, [user]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setDataState('unauthenticated');
      setWallet(null);
      setEarnings([]);
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

  const formatAmount = (value: number | string) =>
    new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(Number(value));

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8 flex flex-wrap items-center gap-3">
          <h1 className="display flex-1 text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <ProvenanceStamp
            source={source}
            label={t('title')}
            method={dataState === 'live' ? statusLine('realData') : undefined}
          />
        </header>

        {dataState !== 'live' && (
          <MarketDataStateNotice
            state={dataState}
            locale={locale}
            detail={dataState === 'error' ? detail : undefined}
            failureKind={failureKind}
            onRetry={() => void load()}
            emptyMessage={statusLine('unavailable')}
          />
        )}

        {dataState === 'live' && wallet && (
          <div className="space-y-8">
            <Card density="compact">
              <h2 className="mb-3 font-medium text-ink">{t('balance')}</h2>
              <p className="num text-3xl font-bold text-forest">{formatAmount(wallet.balance)}</p>
              <dl className="mt-4 space-y-2">
                {(
                  [
                    ['totalEarned', wallet.total_earned],
                    ['totalRedeemed', wallet.total_redeemed],
                  ] as const
                ).map(([field, value]) => (
                  <div key={field} className="flex items-center justify-between">
                    <dt className="text-sm text-ink-soft">{t(field)}</dt>
                    <dd className="num text-sm text-ink">{formatAmount(value)}</dd>
                  </div>
                ))}
                <div className="flex items-center justify-between">
                  <dt className="text-sm text-ink-soft">{t('accountStatus')}</dt>
                  <dd className="text-sm text-ink">
                    {wallet.is_active ? t('active') : t('inactive')}
                  </dd>
                </div>
              </dl>
            </Card>

            <Card density="compact">
              <h2 className="mb-4 font-medium text-ink">{t('earnings')}</h2>
              {earnings.length === 0 ? (
                <p role="status" className="text-sm text-ink-soft">
                  {t('noEarnings')}
                </p>
              ) : (
                <ul className="space-y-3">
                  {earnings.map((entry) => (
                    <li
                      key={earningRowKey(entry)}
                      className="flex items-center justify-between rounded-md border border-line p-3"
                    >
                      <div>
                        <p className="font-medium text-ink">{entry.source}</p>
                        <p className="num text-xs text-ink-soft">
                          {entry.earnings_type} · {entry.processed_at ?? entry.date} ·{' '}
                          {entry.status}
                        </p>
                      </div>
                      <p className="num text-sm font-medium text-forest">
                        {formatAmount(entry.amount)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card density="compact">
              <h2 className="mb-2 font-medium text-ink">{t('title')}</h2>
              <p role="status" className="text-sm text-ink-soft">
                {t('withdrawalUnavailable')}
              </p>
            </Card>
          </div>
        )}
      </div>
    </main>
  );
}
