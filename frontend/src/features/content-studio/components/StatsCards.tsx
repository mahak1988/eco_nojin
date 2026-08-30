/**
 * StatsCards Component
 * =====================
 * @module features/content-studio/components
 */

import { FileText, Globe, Edit3, Calendar } from 'lucide-react';
import type { ContentItem } from '../types';
import { normalizeStatus } from '../utils/formatters';

interface StatsCardsProps {
  items: ContentItem[];
  isLoading?: boolean;
}

export function StatsCards({ items, isLoading }: StatsCardsProps) {
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

  const published = items.filter((i) => normalizeStatus(i.status) === 'published');
  const drafts = items.filter((i) => normalizeStatus(i.status) === 'draft');
  const scheduled = items.filter((i) => normalizeStatus(i.status) === 'scheduled');

  const cards = [
    {
      icon: <FileText size={28} />,
      iconBg: 'rgba(59, 130, 246, 0.15)',
      iconColor: 'var(--accent-info)',
      label: 'Total Content',
      value: items.length.toString(),
    },
    {
      icon: <Globe size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      label: 'Published',
      value: published.length.toString(),
      valueColor: 'var(--accent-primary)',
    },
    {
      icon: <Edit3 size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      label: 'Drafts',
      value: drafts.length.toString(),
      valueColor: 'var(--accent-secondary)',
    },
    {
      icon: <Calendar size={28} />,
      iconBg: 'rgba(139, 92, 246, 0.15)',
      iconColor: 'var(--accent-purple)',
      label: 'Scheduled',
      value: scheduled.length.toString(),
      valueColor: 'var(--accent-purple)',
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
        </div>
      ))}
    </div>
  );
}
