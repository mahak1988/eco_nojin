/**
 * StatsCards Component
 * =====================
 * @module features/telegram-manager/components
 */

import { motion } from 'framer-motion';
import { Bot, Zap, Users, MessageSquare } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { TelegramStats } from '../types';
import { formatNumber } from '../utils/formatters';

interface StatsCardsProps {
  stats: TelegramStats;
}

export function StatsCards({ stats }: StatsCardsProps) {
  const { t } = useTranslation();

  const cards = [
    {
      icon: <Bot size={28} />,
      iconBg: 'rgba(59, 130, 246, 0.15)',
      iconColor: 'var(--accent-info)',
      label: t('telegram.totalBots'),
      value: stats.totalBots.toString(),
    },
    {
      icon: <Zap size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      label: t('telegram.activeBots'),
      value: stats.activeBots.toString(),
      valueColor: 'var(--accent-primary)',
    },
    {
      icon: <Users size={28} />,
      iconBg: 'rgba(139, 92, 246, 0.15)',
      iconColor: 'var(--accent-purple)',
      label: t('telegram.totalUsers'),
      value: formatNumber(stats.totalUsers),
    },
    {
      icon: <MessageSquare size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      label: t('telegram.totalMessages'),
      value: formatNumber(stats.totalMessages),
    },
  ];

  return (
    <div className="grid-4col">
      {cards.map((card, i) => (
        <motion.div
          key={i}
          className="metric-card"
          whileHover={{ scale: 1.02 }}
        >
          <div
            className="metric-icon"
            style={{ background: card.iconBg, color: card.iconColor }}
          >
            {card.icon}
          </div>
          <div className="metric-label">{card.label}</div>
          <div className="metric-value" style={{ color: card.valueColor }}>
            {card.value}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
