// frontend/app/ecowallet/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Wallet, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

interface Transaction {
  id: number;
  type: 'credit' | 'debit';
  amount: number;
  description: string;
  timestamp: string;
}

interface WalletBalance {
  eco_coin: number;
  eco_credit: number;
}

export default function EcoWalletPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // const balanceRes = await apiClient.get('/api/v1/ecowallet/balance');
        // const transactionsRes = await apiClient.get('/api/v1/ecowallet/transactions');
        // setBalance(balanceRes.data);
        // setTransactions(transactionsRes.data);
        // Mock data for demonstration
        setBalance({ eco_coin: 1250.75, eco_credit: 50 });
        setTransactions([
          { id: 1, type: 'credit', amount: 100, description: 'Reward for data contribution', timestamp: '2023-10-28T10:00:00Z' },
          { id: 2, type: 'debit', amount: 25.5, description: 'Purchase seeds', timestamp: '2023-10-27T15:30:00Z' },
          { id: 3, type: 'credit', amount: 50, description: 'Carbon credit earned', timestamp: '2023-10-25T09:15:00Z' },
        ]);
      } catch (err) {
        setError('Failed to load wallet data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchData();
    }
  }, [token]);

  const handleRefresh = () => {
    // Re-fetch data
    if (token) {
      fetchData();
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      // const balanceRes = await apiClient.get('/api/v1/ecowallet/balance');
      // const transactionsRes = await apiClient.get('/api/v1/ecowallet/transactions');
      // setBalance(balanceRes.data);
      // setTransactions(transactionsRes.data);
      // Mock data refresh
      setBalance({ eco_coin: 1250.75, eco_credit: 50 });
    } catch (err) {
      setError('Failed to refresh wallet data.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {t('common_please_log_in')}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700 flex items-center justify-center">
            <Wallet className="h-5 w-5 mr-2" />
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('ecowallet_title')}</h1>

      {loading || !balance ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('ecowallet_balance_coin')}</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{balance.eco_coin.toFixed(2)} EC</div>
              </CardContent>
            </Card>
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('ecowallet_balance_credit')}</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{balance.eco_credit.toFixed(2)} ERC</div>
              </CardContent>
            </Card>
          </div>

          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>{t('ecowallet_recent_transactions')}</CardTitle>
                <Button variant="ghost" size="sm" onClick={handleRefresh}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {transactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between p-4 rounded-lg border" style={{ borderColor: colors.border }}>
                    <div className="flex items-center">
                      {tx.type === 'credit' ? (
                        <TrendingUp className="h-5 w-5 text-green-500 mr-3" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500 mr-3" />
                      )}
                      <div>
                        <p className="font-medium">{tx.description}</p>
                        <p className="text-sm text-muted-foreground">{new Date(tx.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className={`text-right font-medium ${tx.type === 'credit' ? 'text-green-500' : 'text-red-500'}`}>
                      {tx.type === 'credit' ? '+' : '-'}{tx.amount.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}