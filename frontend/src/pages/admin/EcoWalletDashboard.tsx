/**
 * EcoWalletDashboard (Orchestrator)
 * ==================================
 * Main entry point for EcoWallet Command Center.
 *
 * This file is ONLY an orchestrator. All logic is extracted to:
 * - hooks/ (React Query for all API calls)
 * - components/ (extracted UI components)
 * - api/ (API functions)
 * - constants/ (configuration and mock data)
 *
 * Before: 368 lines with anti-patterns
 * After:  ~70 lines of clean orchestration
 *
 * Key improvements:
 * - Math.random removed from render (deterministic chart)
 * - fetch in useEffect → React Query (3 separate queries)
 * - any types removed (proper TypeScript)
 * - Extracted 4 reusable components
 *
 * @module pages/admin/EcoWalletDashboard
 */

import { Wallet, Coins, Gift, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { useEcoWalletStats } from '../../features/eco-wallet/hooks/useEcoWalletStats';
import { useEarningOptions } from '../../features/eco-wallet/hooks/useEarningOptions';
import { useRedemptionOptions } from '../../features/eco-wallet/hooks/useRedemptionOptions';
import { StatsCards } from '../../features/eco-wallet/components/StatsCards';
import { TransactionChart } from '../../features/eco-wallet/components/TransactionChart';
import { OptionsList } from '../../features/eco-wallet/components/OptionsList';
import { EcoWalletErrorBoundary } from '../../features/eco-wallet/components/EcoWalletErrorBoundary';

import './AdminTheme.css';
import './AdminPanelAdvanced.css';

export default function EcoWalletDashboard() {
  const { t } = useTranslation();

  // React Query hooks (auto-loading, auto-error handling)
  const { stats, isLoading: statsLoading, refetch: refetchStats } = useEcoWalletStats();
  const { options: earningOptions, refetch: refetchEarning } = useEarningOptions();
  const { options: redemptionOptions, refetch: refetchRedemption } = useRedemptionOptions();

  const handleRefresh = () => {
    void refetchStats();
    void refetchEarning();
    void refetchRedemption();
  };

  return (
    <EcoWalletErrorBoundary>
      <div className="admin-page-container">
        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Wallet size={32} style={{ color: 'var(--accent-primary)' }} />
              {t('nav.ecowallet', 'EcoWallet Command Center')}
            </h1>
            <p className="page-subtitle">
              {t('crypto.subtitle', 'Monitor eco wallet transactions')}
            </p>
          </div>
          <button className="refresh-btn" onClick={handleRefresh}>
            <RefreshCw size={16} /> {t('common.refresh', 'Refresh')}
          </button>
        </div>

        {/* Stats Cards (with skeleton loading) */}
        <StatsCards stats={stats} isLoading={statsLoading} />

        {/* Transaction Chart (deterministic, no Math.random) */}
        <TransactionChart />

        {/* Options Grid */}
        <div className="grid-2col">
          <OptionsList
            type="earning"
            options={earningOptions}
            title={t('crypto.recentTransactions', 'Earning Options')}
            icon={<Coins size={20} />}
            emptyMessage="No earning options"
          />
          <OptionsList
            type="redemption"
            options={redemptionOptions}
            title={t('crypto.recentTransactions', 'Redemption Options')}
            icon={<Gift size={20} />}
            emptyMessage="No redemption options"
          />
        </div>
      </div>
    </EcoWalletErrorBoundary>
  );
}
