/**
 * CryptoPaymentWidget (Orchestrator)
 * ====================================
 * Main entry point for crypto payment administration widget.
 *
 * This file is ONLY an orchestrator. All logic is extracted to:
 * - hooks/useCryptoWallets.ts (React Query)
 * - hooks/useLiveTransactions.ts (interval management)
 * - hooks/useClipboard.ts (clipboard wrapper)
 * - components/* (extracted UI components)
 *
 * Before: 323 lines with anti-patterns
 * After:  ~90 lines of clean orchestration
 *
 * @module pages/admin/crypto/CryptoPaymentWidget
 */

import { Wallet, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { useCryptoWallets } from '../../../features/crypto-payment/hooks/useCryptoWallets';
import { useLiveTransactions } from '../../../features/crypto-payment/hooks/useLiveTransactions';
import { useClipboard } from '../../../features/crypto-payment/hooks/useClipboard';
import { StatsCards } from '../../../features/crypto-payment/components/StatsCards';
import { WalletCard } from '../../../features/crypto-payment/components/WalletCard';
import { TransactionRow } from '../../../features/crypto-payment/components/TransactionRow';
import { CryptoErrorBoundary } from '../../../features/crypto-payment/components/CryptoErrorBoundary';

import '../../../pages/admin/live/LiveComponents.css';
import '../../../pages/admin/AdminTheme.css';

export default function CryptoPaymentWidget() {
  const { t } = useTranslation();

  // Hooks
  const { wallets, isLoading: walletsLoading } = useCryptoWallets();
  const { transactions, isRunning, refresh } = useLiveTransactions(true);
  const { copiedId, copy } = useClipboard();

  return (
    <CryptoErrorBoundary>
      <div className="admin-page-container">
        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Wallet size={32} style={{ color: 'var(--accent-primary)' }} />
              {t('crypto.title')}
            </h1>
            <p className="page-subtitle">{t('crypto.subtitle')}</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div className="live-indicator">
              <span className="live-dot" />
              {t('common.live')} {isRunning ? '' : '(paused)'}
            </div>
            <button className="refresh-btn" onClick={refresh}>
              <RefreshCw size={16} /> {t('common.refresh')}
            </button>
          </div>
        </div>

        {/* Stats */}
        <StatsCards wallets={wallets} transactions={transactions} />

        {/* Wallets Grid */}
        <div className="grid-3col" style={{ marginBottom: '24px' }}>
          {walletsLoading ? (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
              {t('common.loading')}
            </div>
          ) : (
            wallets.map((wallet) => (
              <WalletCard key={wallet.type} wallet={wallet} copiedId={copiedId} onCopy={copy} />
            ))
          )}
        </div>

        {/* Transactions Table */}
        <div className="chart-container">
          <div className="chart-title">{t('crypto.recentTransactions')}</div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>{t('crypto.amount')}</th>
                <th>USD Value</th>
                <th>From</th>
                <th>{t('crypto.confirmations')}</th>
                <th>{t('crypto.status')}</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx, i) => (
                <TransactionRow key={tx.id} tx={tx} index={i} />
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}
                  >
                    {t('common.loading')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </CryptoErrorBoundary>
  );
}
