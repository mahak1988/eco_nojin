/**
 * StatsCards Component
 * =====================
 * Displays key metrics: total balance, pending count, total received.
 *
 * @module features/crypto-payment/components
 */

import { motion } from 'framer-motion';
import { Wallet, ArrowUpRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { WalletInfo, CryptoTransaction } from '../types';
import { formatUSD } from '../utils/formatters';

interface StatsCardsProps {
  wallets: WalletInfo[];
  transactions: CryptoTransaction[];
}

export function StatsCards({ wallets, transactions }: StatsCardsProps) {
  const { t } = useTranslation();

  const totalUsdValue = wallets.reduce((sum, w) => sum + w.usdValue, 0);
  const pendingCount = transactions.filter((tx) => tx.status === 'pending').length;

  const cards = [
    {
      label: t('crypto.walletBalance'),
      value: formatUSD(totalUsdValue),
      icon: <Wallet size={28} />,
      bg: 'rgba(16, 185, 129, 0.15)',
      color: 'var(--accent-primary)',
      delay: 0,
    },
    {
      label: t('crypto.pendingTx'),
      value: String(pendingCount),
      icon: <ArrowUpRight size={28} />,
      bg: 'rgba(245, 158, 11, 0.15)',
      color: 'var(--accent-secondary)',
      delay: 0.1,
      valueColor: 'var(--accent-secondary)',
    },
    {
      label: t('crypto.totalReceived'),
      value: formatUSD(totalUsdValue),
      icon: <ArrowUpRight size={28} />,
      bg: 'rgba(59, 130, 246, 0.15)',
      color: 'var(--accent-info)',
      delay: 0.2,
    },
  ];

  return (
    <div className="grid-3col">
      {cards.map((card) => (
        <motion.div
          key={card.label}
          className="metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: card.delay }}
        >
          <div
            className="metric-icon"
            style={{ background: card.bg, color: card.color }}
          >
            {card.icon}
          </div>
          <div className="metric-label">{card.label}</div>
          <div
            className="metric-value"
            style={{ fontSize: '24px', color: card.valueColor }}
          >
            {card.value}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
