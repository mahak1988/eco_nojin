'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

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

const MOCK_WALLET: WalletData = {
  balance: 2450000,
  currency: 'IRT',
  reserved: 350000,
  available: 2100000,
  lastUpdated: '2025-09-22T14:30:00Z',
};

const MOCK_TRANSACTIONS: Transaction[] = [
  {
    id: 'tx-001',
    type: 'credit',
    description: 'Market sale payout',
    amount: 890000,
    currency: 'IRT',
    status: 'completed',
    timestamp: '2025-09-22T14:30:00Z',
    reference: '#ORD-001',
  },
  {
    id: 'tx-002',
    type: 'escrow',
    description: 'Escrow lock — Pistachio order',
    amount: -245000,
    currency: 'IRT',
    status: 'pending',
    timestamp: '2025-09-20T09:15:00Z',
    reference: '#ESC-001',
  },
  {
    id: 'tx-003',
    type: 'debit',
    description: 'Platform fee',
    amount: -122500,
    currency: 'IRT',
    status: 'completed',
    timestamp: '2025-09-18T16:45:00Z',
    reference: '#ORD-001',
  },
  {
    id: 'tx-004',
    type: 'release',
    description: 'Escrow release — Saffron order',
    amount: 8900000,
    currency: 'IRT',
    status: 'completed',
    timestamp: '2025-09-15T11:20:00Z',
    reference: '#ESC-001',
  },
];

export default function WalletPage() {
  const t = useTranslations('market.wallet');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [wallet, setWallet] = useState<WalletData>(MOCK_WALLET);
  const [transactions, setTransactions] = useState<Transaction[]>(MOCK_TRANSACTIONS);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [isWithdrawing, setIsWithdrawing] = useState(false);

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
    setIsWithdrawing(true);
    setTimeout(() => {
      alert(t('withdrawalRequested'));
      setWithdrawAmount('');
      setIsWithdrawing(false);
    }, 500);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">{t('lead')}</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2 mb-8">
          <Card density="compact">
            <h2 className="font-medium text-ink mb-3">{t('balance')}</h2>
            <p className="text-3xl font-bold text-forest">{formatPrice(wallet.balance)} ریال</p>
            <p className="text-sm text-ink-soft mt-1">
              {common('lastUpdated')}: {new Date(wallet.lastUpdated).toLocaleDateString()}
            </p>
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
              <label className="block text-sm text-ink-soft mb-1">{t('withdrawAmount')}</label>
              <input
                type="number"
                value={withdrawAmount}
                onChange={e => setWithdrawAmount(e.target.value)}
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
              disabled={!withdrawAmount || Number(withdrawAmount) > wallet.available || isWithdrawing}
              onClick={handleWithdraw}
            >
              {isWithdrawing ? common('processing') : t('withdrawButton')}
            </Button>
          </div>
        </Card>

        <Card density="compact">
          <h2 className="font-medium text-ink mb-4">{t('transactions')}</h2>
          <div className="space-y-3">
            {transactions.map(tx => (
              <div key={tx.id} className="flex items-center justify-between p-3 border border-line rounded-md">
                <div className="flex items-center gap-3">
                  <span className={`flex h-8 w-8 items-center justify-center rounded-full text-lg font-medium ${getTypeColor(tx.type)}`}>
                    {getTypeIcon(tx.type)}
                  </span>
                  <div>
                    <p className="font-medium text-ink">{tx.description}</p>
                    <p className="text-sm text-ink-soft">{new Date(tx.timestamp).toLocaleDateString()}</p>
                    {tx.reference && (
                      <p className="text-xs text-ink-soft">{tx.reference}</p>
                    )}
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
            source="EcoWallet Service"
            verified={true}
            method="Smart contract"
            label={t('walletProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
