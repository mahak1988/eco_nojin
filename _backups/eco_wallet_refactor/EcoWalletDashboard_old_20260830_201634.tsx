import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Wallet, TrendingUp, TrendingDown, Coins, Gift,
  Users, RefreshCw, ArrowUpRight, ArrowDownRight,
  Clock, AlertCircle, CheckCircle, Leaf
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

const API_BASE = 'http://localhost:8000/api/v1';

// Type definitions based on actual API response
interface EarningOption {
  category: string;
  eco_amount: number;
  description: string;
}

interface RedemptionOption {
  category: string;
  eco_amount: number;
  description: string;
}

interface WalletStats {
  total_wallets?: number;
  active_wallets?: number;
  total_earnings?: number;
  total_redemptions?: number;
  pending?: number;
  total_transactions?: number;
}

// Helper to safely extract string from any value
function safeString(value: any, fallback: string = 'N/A'): string {
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toString();
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return String(value);
}

export default function EcoWalletDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<WalletStats | null>(null);
  const [earningOptions, setEarningOptions] = useState<EarningOption[]>([]);
  const [redemptionOptions, setRedemptionOptions] = useState<RedemptionOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = { 
        'Content-Type': 'application/json' 
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const [statsRes, earnRes, redeemRes] = await Promise.all([
        fetch(`${API_BASE}/ecowallet/stats`, { headers }),
        fetch(`${API_BASE}/ecowallet/earning-options`, { headers }),
        fetch(`${API_BASE}/ecowallet/redemption-options`, { headers }),
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }

      if (earnRes.ok) {
        const data = await earnRes.json();
        // Handle both array and object responses
        const options = Array.isArray(data) ? data : (data.options || data.items || []);
        setEarningOptions(options);
      }

      if (redeemRes.ok) {
        const data = await redeemRes.json();
        const options = Array.isArray(data) ? data : (data.options || data.items || []);
        setRedemptionOptions(options);
      }
    } catch (e: any) {
      console.error('Failed to fetch EcoWallet data:', e);
      setError(e.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Generate transaction history for chart (last 30 days)
  const transactionHistory = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    earnings: Math.floor(Math.random() * 5000) + 1000,
    redemptions: Math.floor(Math.random() * 3000) + 500,
  }));

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Wallet size={32} /> {t('nav.ecowallet', 'EcoWallet')}
            </h1>
            <p className="page-subtitle">{t('common.loading', 'Loading...')}</p>
          </div>
        </div>
        <div className="grid-4col">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="metric-card">
              <div className="skeleton skeleton-title"></div>
              <div className="skeleton skeleton-card"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const activeWallets = stats?.active_wallets ?? stats?.total_wallets ?? 0;
  const totalEarnings = stats?.total_earnings ?? 0;
  const totalRedemptions = stats?.total_redemptions ?? 0;
  const pendingTransactions = stats?.pending ?? 0;

  return (
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
        <button className="refresh-btn" onClick={fetchData}>
          <RefreshCw size={16} /> {t('common.refresh', 'Refresh')}
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid-4col">
        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <Wallet size={28} />
          </div>
          <div className="metric-label">{t('crypto.walletBalance', 'Active Wallets')}</div>
          <div className="metric-value">{activeWallets.toLocaleString()}</div>
          <div className="metric-change positive">
            <TrendingUp size={12} /> +12%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <Coins size={28} />
          </div>
          <div className="metric-label">{t('crypto.totalReceived', 'Total Earnings')}</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {totalEarnings.toLocaleString('fa-IR')}
          </div>
          <div className="metric-change positive">
            <ArrowUpRight size={12} /> +24%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
            <Gift size={28} />
          </div>
          <div className="metric-label">{t('telegram.totalMessages', 'Redemptions')}</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {totalRedemptions.toLocaleString('fa-IR')}
          </div>
          <div className="metric-change negative">
            <ArrowDownRight size={12} /> Active
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-danger)' }}>
            <Clock size={28} />
          </div>
          <div className="metric-label">{t('crypto.pendingTx', 'Pending')}</div>
          <div className="metric-value">{pendingTransactions}</div>
          <div className="metric-change negative">
            <AlertCircle size={12} /> Attention
          </div>
        </div>
      </div>

      {/* Transaction Flow Chart */}
      <div className="chart-container">
        <div className="chart-title">
          <TrendingUp size={20} />
          Earnings vs Redemptions (30 days)
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={transactionHistory}>
            <defs>
              <linearGradient id="earningsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="redemptionsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
            <YAxis stroke="var(--text-muted)" fontSize={11} />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-card-solid)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
              }}
            />
            <Legend />
            <Area type="monotone" dataKey="earnings" stroke="#10b981" fillOpacity={1} fill="url(#earningsGradient)" name="Earnings" />
            <Area type="monotone" dataKey="redemptions" stroke="#8b5cf6" fillOpacity={1} fill="url(#redemptionsGradient)" name="Redemptions" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Options Grid */}
      <div className="grid-2col">
        {/* Earning Options */}
        <div className="chart-container">
          <div className="chart-title">
            <Coins size={20} />
            {t('crypto.recentTransactions', 'Earning Options')} ({earningOptions.length})
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {earningOptions.length === 0 ? (
              <div className="empty-state-enhanced" style={{ padding: '40px' }}>
                <div className="icon">🪙</div>
                <div className="title">No earning options</div>
              </div>
            ) : (
              earningOptions.map((option, i) => {
                // Create unique key - prefer category, fallback to index
                const uniqueKey = option.category 
                  ? `earning-${option.category}-${i}` 
                  : `earning-${i}`;
                
                return (
                  <div 
                    key={uniqueKey} 
                    className="transaction-row" 
                    style={{ borderBottom: '1px solid var(--border-color)' }}
                  >
                    <div style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '12px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: 'var(--accent-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      <Leaf size={22} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {safeString(option.category, 'Earning Option')}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {safeString(option.description, 'Earn eco-tokens')}
                      </div>
                    </div>
                    <div style={{ textAlign: 'end', flexShrink: 0 }}>
                      <div style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '16px' }}>
                        +{option.eco_amount ?? 0}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>tokens</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Redemption Options */}
        <div className="chart-container">
          <div className="chart-title">
            <Gift size={20} />
            {t('crypto.recentTransactions', 'Redemption Options')} ({redemptionOptions.length})
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {redemptionOptions.length === 0 ? (
              <div className="empty-state-enhanced" style={{ padding: '40px' }}>
                <div className="icon">🎁</div>
                <div className="title">No redemption options</div>
              </div>
            ) : (
              redemptionOptions.map((option, i) => {
                const uniqueKey = option.category 
                  ? `redemption-${option.category}-${i}` 
                  : `redemption-${i}`;
                
                return (
                  <div 
                    key={uniqueKey} 
                    className="transaction-row" 
                    style={{ borderBottom: '1px solid var(--border-color)' }}
                  >
                    <div style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '12px',
                      background: 'rgba(139, 92, 246, 0.15)',
                      color: 'var(--accent-purple)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}>
                      <Gift size={22} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {safeString(option.category, 'Redemption')}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {safeString(option.description, 'Redeem tokens')}
                      </div>
                    </div>
                    <div style={{ textAlign: 'end', flexShrink: 0 }}>
                      <div style={{ fontWeight: 700, color: 'var(--accent-purple)', fontSize: '16px' }}>
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
      </div>
    </div>
  );
}
