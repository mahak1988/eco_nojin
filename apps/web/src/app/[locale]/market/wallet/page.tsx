'use client';

import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

interface Transaction {
  id: string;
  type: 'credit' | 'debit' | 'escrow' | 'release';
  description: string;
  amount: number;
  currency: string;
  status: 'completed' | 'pending' | 'failed';
  timestamp: string;
  reference?: string;
}

interface WalletData {
  balance: number;
  currency: string;
  reserved: number;
  available: number;
  lastUpdated: string;
}

type WalletStateResponse = {
  user_id: string;
  balance: number | string;
  total_earned: number | string;
  total_redeemed: number | string;
  is_active: boolean;
};

type EarningsResponse = {
  date: string;
  earnings_type: string;
  amount: string;
  source: string;
  status: string;
  processed_at: string | null;
};

const EMPTY_WALLET: WalletData = {
  balance: 0,
  currency: '',
  reserved: 0,
  available: 0,
  lastUpdated: '',
};

export default function WalletPage() {
  const t = useTranslations('market.wallet');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1] || 'fa';

  const { user, loading: authLoading } = useAuth();
  const [wallet, setWallet] = useState<WalletData>(EMPTY_WALLET);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [dataState, setDataState] = useState<
    'loading' | 'ready' | 'unauthenticated' | 'unavailable'
  >('loading');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const isWithdrawing = false;
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setDataState('unauthenticated');
      return;
    }
    void Promise.all([
      apiGet<WalletStateResponse>(`/api/v1/ecowallet/wallet/${encodeURIComponent(user.id)}`),
      apiGet<EarningsResponse[]>(
        `/api/v1/ecowallet/earnings?user_id=${encodeURIComponent(user.id)}`,
      ),
    ]).then(([walletResult, earningsResult]) => {
      if (!walletResult.ok || !earningsResult.ok) {
        setDataState('unavailable');
        return;
      }
      const balance = Number(walletResult.data.balance);
      const reserved = Number(walletResult.data.total_redeemed);
      setWallet({
        balance,
        currency: 'ECO',
        reserved,
        available: balance - reserved,
        lastUpdated: '',
      });
      setTransactions(
        earningsResult.data.map((earning) => ({
          id: `${earning.date}-${earning.earnings_type}`,
          type: 'credit',
          description: earning.source,
          amount: Number(earning.amount),
          currency: 'ECO',
          status: earning.status === 'completed' ? 'completed' : 'pending',
          timestamp: earning.processed_at ?? earning.date,
        })),
      );
      setDataState('ready');
    });
  }, [authLoading, user]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'credit':
        return '+';
      case 'release':
        return '↗';
      case 'debit':
        return '-';
      default:
        return '=';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'credit':
      case 'release':
        return 'text-forest';
      case 'debit':
      case 'escrow':
        return 'text-copper';
      default:
        return 'text-ink';
    }
  };

  const handleWithdraw = () => {
    setError(t('dataUnavailable'));
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">{t('lead')}</p>
        </header>
        {error && (
          <p role="alert" className="mb-6 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-2 mb-8">
          <Card density="compact">
            <h2 className="font-medium text-ink mb-3">{t('balance')}</h2>
            <p className="text-3xl font-bold text-forest">{formatPrice(wallet.balance)} ریال</p>
            {dataState === 'unavailable' && (
              <p role="status" className="mt-2 text-sm text-ink-soft">
                {t('dataUnavailable')}
              </p>
            )}
          </Card>

          <Card density="compact">
            <h2 className="font-medium text-ink mb-3">{t('available')}</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-ink-soft">{t('available')}</span>
                <span className="font-medium text-ink">{formatPrice(wallet.available)} ریال</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-soft">{t('reserved')}</span>
                <span className="font-medium text-ink">{formatPrice(wallet.reserved)} ریال</span>
              </div>
            </div>
          </Card>
        </div>

        <Card density="compact" className="mb-8">
          <h2 className="font-medium text-ink mb-4">{t('withdraw')}</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="withdraw-amount" className="block text-sm text-ink-soft mb-1">
                {t('withdrawAmount')}
              </label>
              <input
                id="withdraw-amount"
                type="number"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                placeholder={t('withdrawPlaceholder')}
                className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                max={wallet.available}
                min="1"
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-ink-soft">{t('maxWithdraw')}</span>
              <span className="font-medium text-ink">{formatPrice(wallet.available)} ریال</span>
            </div>

            <Button
              variant="primary"
              disabled={
                dataState !== 'ready' ||
                !withdrawAmount ||
                Number(withdrawAmount) > wallet.available ||
                isWithdrawing
              }
              onClick={handleWithdraw}
            >
              {isWithdrawing ? common('processing') : t('withdrawButton')}
            </Button>
          </div>
        </Card>

        <Card density="compact">
          <h2 className="font-medium text-ink mb-4">{t('transactions')}</h2>
          <div className="space-y-3">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between p-3 border border-line rounded-md"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-lg font-medium ${getTypeColor(tx.type)}`}
                  >
                    {getTypeIcon(tx.type)}
                  </span>
                  <div>
                    <p className="font-medium text-ink">{tx.description}</p>
                    <p className="text-sm text-ink-soft">
                      {new Date(tx.timestamp).toLocaleDateString()}
                    </p>
                    {tx.reference && <p className="text-xs text-ink-soft">{tx.reference}</p>}
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-medium ${tx.amount > 0 ? 'text-forest' : 'text-copper'}`}>
                    {formatPrice(Math.abs(tx.amount))} ریال
                  </p>
                  <span className="text-xs text-ink-soft capitalize">{tx.status}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card density="compact" className="mt-8">
          <ProvenanceStamp
            source={
              user ? `/api/v1/ecowallet/wallet/${encodeURIComponent(user.id)}` : '/api/v1/ecowallet'
            }
            verified={false}
            label={t('walletProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
