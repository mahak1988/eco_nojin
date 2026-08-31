import { useState } from 'react';
import './AdminTheme.css';

export default function AdminFinance() {
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d');

  const financialData = {
    totalRevenue: 125450000,
    totalExpenses: 45230000,
    netProfit: 80220000,
    pendingPayouts: 12500000,
    transactions: [
      {
        id: 1,
        type: 'payment',
        amount: 2500000,
        user: 'farmer_123',
        date: '2026-08-27',
        status: 'completed',
      },
      {
        id: 2,
        type: 'subscription',
        amount: 1500000,
        user: 'farmer_456',
        date: '2026-08-26',
        status: 'completed',
      },
      {
        id: 3,
        type: 'marketplace',
        amount: 3200000,
        user: 'buyer_789',
        date: '2026-08-26',
        status: 'pending',
      },
      {
        id: 4,
        type: 'payment',
        amount: 1800000,
        user: 'farmer_321',
        date: '2026-08-25',
        status: 'completed',
      },
    ],
    revenueByCategory: [
      { category: 'Subscriptions', amount: 45000000, percentage: 36 },
      { category: 'Marketplace', amount: 38000000, percentage: 30 },
      { category: 'Tours', amount: 25000000, percentage: 20 },
      { category: 'Premium Features', amount: 17450000, percentage: 14 },
    ],
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 }).format(amount) + ' IRR';
  };

  return (
    <div>
      <div className="info-banner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 800 }}>
              Finance Dashboard
            </h2>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>
              Platform revenue, expenses, and financial analytics
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['7d', '30d', '90d', '1y'] as const).map((period) => (
              <button
                key={period}
                className={'filter-chip' + (selectedPeriod === period ? ' active' : '')}
                onClick={() => setSelectedPeriod(period)}
              >
                {period}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label">Total Revenue</div>
          <div className="stat-value" style={{ fontSize: '24px' }}>
            {formatCurrency(financialData.totalRevenue)}
          </div>
          <span className="trend-badge up" style={{ marginTop: '8px' }}>
            +18%
          </span>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Expenses</div>
          <div className="stat-value" style={{ fontSize: '24px' }}>
            {formatCurrency(financialData.totalExpenses)}
          </div>
          <span className="trend-badge down" style={{ marginTop: '8px' }}>
            +5%
          </span>
        </div>
        <div className="stat-card">
          <div className="stat-label">Net Profit</div>
          <div className="stat-value" style={{ fontSize: '24px', color: 'var(--accent-primary)' }}>
            {formatCurrency(financialData.netProfit)}
          </div>
          <span className="trend-badge up" style={{ marginTop: '8px' }}>
            +24%
          </span>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Payouts</div>
          <div className="stat-value" style={{ fontSize: '24px' }}>
            {formatCurrency(financialData.pendingPayouts)}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div className="section-title" style={{ marginBottom: '24px' }}>
            Revenue by Category
          </div>
          {financialData.revenueByCategory.map((item, i) => (
            <div key={i} style={{ marginBottom: '20px' }}>
              <div
                style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}
              >
                <span style={{ color: 'var(--text-primary)', fontWeight: 500, fontSize: '14px' }}>
                  {item.category}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                  {item.percentage}%
                </span>
              </div>
              <div
                style={{
                  height: '8px',
                  background: 'var(--border-color)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: item.percentage + '%',
                    background:
                      'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                    borderRadius: '4px',
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="glass-card">
          <div className="section-header" style={{ padding: '24px 24px 0 24px' }}>
            <div className="section-title">Recent Transactions</div>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Amount</th>
                <th>User</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {financialData.transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>
                    <span className="status-badge info">{tx.type}</span>
                  </td>
                  <td
                    style={{
                      color: 'var(--accent-primary)',
                      fontWeight: 600,
                      fontFamily: 'monospace',
                    }}
                  >
                    {formatCurrency(tx.amount)}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{tx.user}</td>
                  <td>
                    <span
                      className={
                        'status-badge ' + (tx.status === 'completed' ? 'success' : 'warning')
                      }
                    >
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
