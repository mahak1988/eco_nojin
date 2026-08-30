/**
 * StatsCards Component
 * =====================
 * @module features/security/components
 */

import {
  Activity, CheckCircle, AlertTriangle, Shield,
  TrendingUp, TrendingDown,
} from 'lucide-react';
import type { SecurityStats } from '../types';
import { getScoreColor } from '../utils/formatters';

interface StatsCardsProps {
  stats: SecurityStats;
  isLoading?: boolean;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid-4col">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-card"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      icon: <Activity size={28} />,
      iconBg: 'rgba(59, 130, 246, 0.15)',
      iconColor: 'var(--accent-info)',
      label: 'Total Events',
      value: stats.totalEvents.toString(),
      changeIcon: <TrendingUp size={12} />,
      changeLabel: 'Live',
      changeClass: 'positive',
    },
    {
      icon: <CheckCircle size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      label: 'Success Rate',
      value: `${stats.successRate}%`,
      valueColor: 'var(--accent-primary)',
      changeIcon: <TrendingUp size={12} />,
      changeLabel: `${stats.successCount} successful`,
      changeClass: 'positive',
    },
    {
      icon: <AlertTriangle size={28} />,
      iconBg: 'rgba(239, 68, 68, 0.15)',
      iconColor: 'var(--accent-danger)',
      label: 'Failed Attempts',
      value: stats.failedCount.toString(),
      valueColor: 'var(--accent-danger)',
      changeIcon: <TrendingDown size={12} />,
      changeLabel: `${stats.uniqueFailedIPs} unique IPs`,
      changeClass: 'negative',
    },
    {
      icon: <Shield size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      label: 'Security Score',
      value: stats.securityScore.toString(),
      valueColor: getScoreColor(stats.securityScore),
      showProgress: true,
    },
  ];

  return (
    <div className="grid-4col">
      {cards.map((card, i) => (
        <div key={i} className="metric-card">
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
          {card.changeLabel && (
            <div className={`metric-change ${card.changeClass}`}>
              {card.changeIcon} {card.changeLabel}
            </div>
          )}
          {card.showProgress && (
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${stats.securityScore}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
