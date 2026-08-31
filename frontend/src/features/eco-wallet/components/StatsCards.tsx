/**
 * StatsCards Component
 * =====================
 * Displays 4 key metric cards for EcoWallet.
 *
 * @module features/eco-wallet/components
 */

import {
  Wallet,
  TrendingUp,
  Coins,
  Gift,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  AlertCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { WalletStats } from '../types';
import { formatNumber, safeNumber } from '../utils/formatters';

interface StatsCardsProps {
  stats: WalletStats | null;
  isLoading?: boolean;
}

interface MetricCardConfig {
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  labelKey: string;
  labelFallback: string;
  value: string;
  changeIcon: React.ReactNode;
  changeLabel: string;
  changeClass: 'positive' | 'negative';
  fontSize?: string;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="grid-4col">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-card"></div>
          </div>
        ))}
      </div>
    );
  }

  const activeWallets = safeNumber(stats?.active_wallets ?? stats?.total_wallets);
  const totalEarnings = safeNumber(stats?.total_earnings);
  const totalRedemptions = safeNumber(stats?.total_redemptions);
  const pending = safeNumber(stats?.pending);

  const cards: MetricCardConfig[] = [
    {
      icon: <Wallet size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      labelKey: 'crypto.walletBalance',
      labelFallback: 'Active Wallets',
      value: activeWallets.toLocaleString(),
      changeIcon: <TrendingUp size={12} />,
      changeLabel: '+12%',
      changeClass: 'positive',
    },
    {
      icon: <Coins size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      labelKey: 'crypto.totalReceived',
      labelFallback: 'Total Earnings',
      value: formatNumber(totalEarnings),
      changeIcon: <ArrowUpRight size={12} />,
      changeLabel: '+24%',
      changeClass: 'positive',
      fontSize: '24px',
    },
    {
      icon: <Gift size={28} />,
      iconBg: 'rgba(139, 92, 246, 0.15)',
      iconColor: 'var(--accent-purple)',
      labelKey: 'telegram.totalMessages',
      labelFallback: 'Redemptions',
      value: formatNumber(totalRedemptions),
      changeIcon: <ArrowDownRight size={12} />,
      changeLabel: 'Active',
      changeClass: 'negative',
      fontSize: '24px',
    },
    {
      icon: <Clock size={28} />,
      iconBg: 'rgba(239, 68, 68, 0.15)',
      iconColor: 'var(--accent-danger)',
      labelKey: 'crypto.pendingTx',
      labelFallback: 'Pending',
      value: pending.toString(),
      changeIcon: <AlertCircle size={12} />,
      changeLabel: 'Attention',
      changeClass: 'negative',
    },
  ];

  return (
    <div className="grid-4col">
      {cards.map((card, i) => (
        <div key={i} className="metric-card">
          <div className="metric-icon" style={{ background: card.iconBg, color: card.iconColor }}>
            {card.icon}
          </div>
          <div className="metric-label">{t(card.labelKey, card.labelFallback)}</div>
          <div className="metric-value" style={{ fontSize: card.fontSize }}>
            {card.value}
          </div>
          <div className={`metric-change ${card.changeClass}`}>
            {card.changeIcon} {card.changeLabel}
          </div>
        </div>
      ))}
    </div>
  );
}
