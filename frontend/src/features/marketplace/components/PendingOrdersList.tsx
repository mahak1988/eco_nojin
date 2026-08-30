/**
 * PendingOrdersList Component
 * =============================
 * @module features/marketplace/components
 */

import { AlertCircle, CheckCircle } from 'lucide-react';
import type { Order } from '../types';
import { LIMITS } from '../constants/config';
import { formatCurrency, truncateId, getOrderAmount } from '../utils/formatters';

interface PendingOrdersListProps {
  pendingOrders: Order[];
  onConfirm: (orderId: string) => void;
  isConfirming?: boolean;
}

export function PendingOrdersList({
  pendingOrders,
  onConfirm,
  isConfirming,
}: PendingOrdersListProps) {
  const displayedOrders = pendingOrders.slice(0, LIMITS.pendingOrdersDisplay);

  return (
    <div className="chart-container">
      <div className="chart-title">
        <AlertCircle size={20} />
        Pending Orders ({pendingOrders.length})
      </div>
      <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
        {pendingOrders.length === 0 ? (
          <div
            className="empty-state-enhanced"
            style={{ padding: '40px 20px' }}
          >
            <div className="icon" style={{ fontSize: '48px' }}>
              ✅
            </div>
            <div className="title">All caught up!</div>
            <div>No pending orders</div>
          </div>
        ) : (
          displayedOrders.map((order) => (
            <div
              key={order.id}
              className="transaction-row"
              style={{ borderBottom: '1px solid var(--border-color)' }}
            >
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                  }}
                >
                  Order #{truncateId(order.id)}
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                    marginTop: '2px',
                  }}
                >
                  {formatCurrency(getOrderAmount(order))} IRR
                </div>
              </div>
              <button
                className="btn-primary"
                style={{ padding: '6px 14px', fontSize: '12px' }}
                onClick={() => onConfirm(order.id)}
                disabled={isConfirming}
              >
                <CheckCircle size={14} style={{ marginRight: '4px' }} />
                Confirm
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
