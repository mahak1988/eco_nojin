/**
 * StatsCards Component
 * =====================
 * @module features/marketplace/components
 */

import {
  Package, ShoppingBag, DollarSign, Star,
  TrendingUp, Clock,
} from 'lucide-react';
import type { Order, MarketplaceStats } from '../types';
import type { DerivedOrderData } from '../types';
import { formatCurrency } from '../utils/formatters';

interface StatsCardsProps {
  products: Product[];
  derived: DerivedOrderData;
  isLoading?: boolean;
}

// Local re-import for simplicity
type Product = import('../types').Product;

export function StatsCards({
  products,
  derived,
  isLoading,
}: StatsCardsProps) {
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

  const cards = [
    {
      icon: <Package size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      label: 'Total Products',
      value: products.length.toString(),
      changeIcon: <TrendingUp size={12} />,
      changeLabel: 'Active',
      changeClass: 'positive',
    },
    {
      icon: <ShoppingBag size={28} />,
      iconBg: 'rgba(59, 130, 246, 0.15)',
      iconColor: 'var(--accent-info)',
      label: 'Total Orders',
      value: derived.pendingOrders.length.toString(),
      changeIcon: <Clock size={12} />,
      changeLabel: `${derived.pendingOrders.length} pending`,
      changeClass: 'positive',
    },
    {
      icon: <DollarSign size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      label: 'Total Revenue',
      value: `${formatCurrency(derived.totalRevenue)} IRR`,
      changeIcon: <TrendingUp size={12} />,
      changeLabel: '+18%',
      changeClass: 'positive',
      fontSize: '24px',
    },
    {
      icon: <Star size={28} />,
      iconBg: 'rgba(139, 92, 246, 0.15)',
      iconColor: 'var(--accent-purple)',
      label: 'Avg Order Value',
      value: `${formatCurrency(derived.avgOrderValue)} IRR`,
      fontSize: '24px',
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
          <div className="metric-value" style={{ fontSize: card.fontSize }}>
            {card.value}
          </div>
          {card.changeLabel && (
            <div className={`metric-change ${card.changeClass || 'positive'}`}>
              {card.changeIcon} {card.changeLabel}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
