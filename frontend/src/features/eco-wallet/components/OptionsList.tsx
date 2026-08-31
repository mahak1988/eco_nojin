/**
 * OptionsList Component
 * ======================
 * Generic reusable list for earning/redemption options.
 *
 * Single Responsibility: Render a list of options with icon and amount.
 *
 * @module features/eco-wallet/components
 */

import { Leaf, Gift } from 'lucide-react';
import type { EarningOption, RedemptionOption } from '../types';
import { safeString } from '../utils/formatters';

type OptionType = 'earning' | 'redemption';

interface OptionsListProps {
  type: OptionType;
  options: EarningOption[] | RedemptionOption[];
  title: string;
  icon: React.ReactNode;
  emptyMessage: string;
}

export function OptionsList({ type, options, title, icon, emptyMessage }: OptionsListProps) {
  const iconBg = type === 'earning' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(139, 92, 246, 0.15)';
  const iconColor = type === 'earning' ? 'var(--accent-secondary)' : 'var(--accent-purple)';
  const amountColor = type === 'earning' ? 'var(--accent-primary)' : 'var(--accent-purple)';
  const ItemIcon = type === 'earning' ? Leaf : Gift;
  const prefix = type === 'earning' ? '+' : '';

  return (
    <div className="chart-container">
      <div className="chart-title">
        {icon} {title} ({options.length})
      </div>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {options.length === 0 ? (
          <div className="empty-state-enhanced" style={{ padding: '40px' }}>
            <div className="icon">🎯</div>
            <div className="title">{emptyMessage}</div>
          </div>
        ) : (
          options.map((option, i) => {
            const uniqueKey = option.category ? `${type}-${option.category}-${i}` : `${type}-${i}`;

            return (
              <div
                key={uniqueKey}
                className="transaction-row"
                style={{ borderBottom: '1px solid var(--border-color)' }}
              >
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    background: iconBg,
                    color: iconColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <ItemIcon size={22} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {safeString(option.category, 'Option')}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-muted)',
                      marginTop: '2px',
                    }}
                  >
                    {safeString(option.description, 'Description')}
                  </div>
                </div>
                <div style={{ textAlign: 'end', flexShrink: 0 }}>
                  <div
                    style={{
                      fontWeight: 700,
                      color: amountColor,
                      fontSize: '16px',
                    }}
                  >
                    {prefix}
                    {option.eco_amount ?? 0}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>tokens</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
